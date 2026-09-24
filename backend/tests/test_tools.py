from unittest.mock import MagicMock
import io
import subprocess

import pytest

from app.agent.state import AgentState
from app.agent.planner import Planner
from app.config import Settings
from app.models import Goal
from app.security.sandbox import run_tests
from app.tools.llm_tool import LLMTool, ReviewAnalysis, Explanation
from app.tools.base import ToolError
from app.tools.source_inspection_tool import verify_issue
from app.analyzers.python_analyzer import analyze_python


def test_no_host_execution(tmp_path, monkeypatch):
    spawn = MagicMock(side_effect=AssertionError("Host subprocess must not be called"))
    monkeypatch.setattr("subprocess.Popen", spawn)
    result = run_tests(tmp_path, Settings(_env_file=None, enable_sandbox=False))
    assert result.status == "blocked"
    spawn.assert_not_called()


def test_missing_docker(tmp_path, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: None)
    with pytest.raises(ToolError, match="Docker"):
        run_tests(tmp_path, Settings(_env_file=None, enable_sandbox=True))


def test_evidence_verification(tmp_path):
    source = "def bad(items=[]):\n    return items\n"
    (tmp_path / "a.py").write_text(source)
    issue = analyze_python("a.py", source)[0]
    assert verify_issue(tmp_path, issue, 1000)
    assert not verify_issue(tmp_path, issue.model_copy(update={"line": 99}), 1000)
    assert not verify_issue(tmp_path, issue.model_copy(update={"file": "../secret"}), 1000)


def test_structured_llm_response(tmp_path, monkeypatch):
    goal = Goal(repository_url="https://github.com/test/repo")
    state = AgentState(goal, tmp_path, Planner().create(goal))
    state.issues = analyze_python("a.py", "def bad(a=[]):\n    return a\n")
    client = MagicMock()
    client.__enter__.return_value = client
    client.responses.parse.return_value.output_parsed = ReviewAnalysis(explanations=[
        Explanation(issue_index=0, explanation="Shared default persists across calls.", suggested_fix="Use None.")])
    monkeypatch.setattr("app.tools.llm_tool.OpenAI", lambda **kwargs: client)
    tool = LLMTool()
    result = tool.execute(state, Settings(_env_file=None, openai_api_key="test-key"), tool.input_schema())
    assert result.data["explanations"][0]["issue_index"] == 0
    client.responses.parse.return_value.output_parsed = ReviewAnalysis(explanations=[
        Explanation(issue_index=100, explanation="Invalid ID", suggested_fix="Invalid")])
    with pytest.raises(ToolError, match="unknown"):
        tool.execute(state, Settings(_env_file=None, openai_api_key="test-key"), tool.input_schema())


@pytest.mark.parametrize("code,output,status", [(0, b"2 passed in 0.1s", "passed"),
                                                (1, b"1 failed, 1 passed in 0.1s", "failed"),
                                                (5, b"no tests ran", "not_available")])
def test_sandbox_result_parser(tmp_path, monkeypatch, code, output, status):
    process = MagicMock(returncode=code, stdout=io.BytesIO(output))
    spawn = MagicMock(return_value=process)
    cleanup = MagicMock()
    monkeypatch.setattr("shutil.which", lambda _: "docker")
    monkeypatch.setattr("subprocess.Popen", spawn)
    monkeypatch.setattr("subprocess.run", cleanup)
    result = run_tests(tmp_path, Settings(_env_file=None, enable_sandbox=True))
    assert result.status == status
    assert spawn.call_args.args[0][:2] == ["docker", "run"]
    assert spawn.call_args.kwargs["shell"] is False
    assert cleanup.call_args.args[0][:3] == ["docker", "rm", "-f"]


def test_sandbox_timeout_cleanup(tmp_path, monkeypatch):
    process = MagicMock(stdout=io.BytesIO(b""))
    process.wait.side_effect = subprocess.TimeoutExpired("docker", 45)
    cleanup = MagicMock()
    monkeypatch.setattr("shutil.which", lambda _: "docker")
    monkeypatch.setattr("subprocess.Popen", lambda *a, **kw: process)
    monkeypatch.setattr("subprocess.run", cleanup)
    with pytest.raises(ToolError) as exc:
        run_tests(tmp_path, Settings(_env_file=None, enable_sandbox=True))
    assert exc.value.category == "timeout"
    process.kill.assert_called_once()
    assert cleanup.call_args.args[0][:3] == ["docker", "rm", "-f"]
