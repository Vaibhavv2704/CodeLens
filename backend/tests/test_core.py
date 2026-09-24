import io
import tarfile

import pytest
from pydantic import ValidationError

from app.agent.planner import Planner
from app.agent.recovery import RecoveryEngine
from app.agent.validator import ResultValidator
from app.analyzers.python_analyzer import analyze_python
from app.config import Settings
from app.models import Goal, TestResult as RunResult
from app.security.command_policy import allowed_test_command
from app.security.paths import read_source, safe_path
from app.security.sandbox import docker_command
from app.tools.base import ToolError
from app.tools.github_tool import extract_snapshot


@pytest.mark.parametrize("url", ["http://github.com/a/b", "https://evil.com/a/b", "https://github.com/a/../b",
                                  "https://github.com/a/b?x=1", "https://user@github.com/a/b", "file:///tmp/a"])
def test_bad_urls(url):
    with pytest.raises(ValidationError):
        Goal(repository_url=url)


def test_url_and_planner():
    goal = Goal(repository_url="https://github.com/a/b.git")
    assert goal.repository_url == "https://github.com/a/b"
    plan = Planner().create(goal, {"languages": ["Python"]})
    assert plan.steps[2].description == "Analyze Python AST"
    assert len(plan.steps) == 7
    plan.steps[1].id = 12
    with pytest.raises(ValidationError):
        type(plan).model_validate(plan.model_dump())


def test_ast_rules():
    issues = analyze_python("bad.py", "def bad(items=[]):\n    try:\n        return eval('1')\n    except:\n        pass\n")
    assert {i.title for i in issues} == {"Mutable default argument", "Bare exception handler",
                                       "Dynamic eval requires input validation"}
    assert issues[0].line == 1
    assert analyze_python("ok.py", "def add(a, b):\n    return a + b\n") == []


@pytest.mark.parametrize("path", ["../secret", "/etc/passwd", "C:/secrets", "x/../../secret", "x\\y", "NUL.txt"])
def test_path_policy(tmp_path, path):
    with pytest.raises(ToolError, match="path|Path"):
        safe_path(tmp_path, path)


def test_binary_and_size(tmp_path):
    (tmp_path / "a.py").write_bytes(b"x\x00y")
    with pytest.raises(ToolError, match="Binary"):
        read_source(tmp_path, "a.py")
    with pytest.raises(ToolError, match="size"):
        read_source(tmp_path, "a.py", 1)


def archive(name, content=b"hello", kind=tarfile.REGTYPE):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        info = tarfile.TarInfo(name)
        info.type, info.size = kind, len(content)
        tar.addfile(info, io.BytesIO(content))
    return buffer.getvalue()


@pytest.mark.parametrize("name,kind", [("repo/../../secret", tarfile.REGTYPE), ("repo/link", tarfile.SYMTYPE)])
def test_malicious_archive(tmp_path, name, kind):
    with pytest.raises(ToolError):
        extract_snapshot(archive(name, kind=kind), tmp_path, Settings(_env_file=None))


def test_valid_archive(tmp_path):
    extract_snapshot(archive("repo/main.py"), tmp_path, Settings(_env_file=None))
    assert (tmp_path / "main.py").read_text() == "hello"


def test_validator_and_recovery():
    with pytest.raises(ToolError) as exc:
        ResultValidator().validate("static_analysis", {"observation": "ok", "data": {}})
    assert exc.value.category == "invalid_tool_output"
    recovery = RecoveryEngine()
    assert recovery.decide(exc.value, 0, "static_analysis") == "retry"
    assert recovery.decide(exc.value, 2, "static_analysis") == "fallback"
    assert recovery.decide(ToolError("security_block", "blocked"), 0, "test_runner") == "fallback"
    assert recovery.decide(ToolError("security_block", "blocked"), 0, "github") == "stop"


def test_inconsistent_test_result():
    with pytest.raises(ValidationError):
        RunResult(status="failed", passed=10)
    with pytest.raises(ValidationError):
        RunResult(status="passed", passed=10, failed=2)


def test_command_policy(tmp_path):
    with pytest.raises(ToolError):
        allowed_test_command("curl | bash")
    command = docker_command(tmp_path, "review-sandbox:local", "test")
    for arg in ["--network=none", "--read-only", "--cap-drop=ALL", "--memory=256m", "--pids-limit=64"]:
        assert arg in command
    assert not any("docker.sock" in arg for arg in command)
