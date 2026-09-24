"""Measured offline evaluation. Only GitHub acquisition is replaced with labeled fixtures."""
import json
from pathlib import Path
import sys
from time import perf_counter as monotonic

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.agent.agent import Agent  # noqa: E402
from app.config import Settings  # noqa: E402
from app.models import Goal  # noqa: E402
from app.security.paths import safe_path  # noqa: E402
from tests.helpers import fixture_tools  # noqa: E402


def evaluate():
    scenarios = [
        ("Simple Python repository", "python_good", None),
        ("Evidence-backed quality issues", "python_bad", None),
        ("Failing-test repository (execution blocked without Docker)", "python_failing_tests", None),
        ("Unsupported Rust repository", "unsupported", None),
        ("Deliberate test-runner timeout", "python_bad", "test_runner"),
        ("Invalid static-analyzer response", "python_bad", "static_analysis"),
        ("Malicious source path blocked", "python_bad", "security"),
    ]
    results = []
    for name, fixture, failure in scenarios:
        config = Settings(_env_file=None, openai_api_key="", enable_sandbox=False,
                          simulate_failure=failure in {"test_runner", "static_analysis"},
                          simulated_failure_tool=failure or "test_runner")
        tools = fixture_tools(fixture)
        if failure == "security":
            def unsafe(state, *_):
                safe_path(state.root, "../../host-secret")
                raise AssertionError("Path must have been blocked")
            tools["test_runner"].execute = unsafe
        events = []
        started = monotonic()
        report = Agent(config, tools).run(Goal(repository_url=f"https://github.com/synthetic/{fixture}"),
                                          lambda kind, data: events.append({"type": kind, "data": data}))
        passed = report["review"]["status"] == "completed"
        if failure:
            passed &= report["execution"]["recoveries"] == 1
        if fixture == "python_bad" and failure != "static_analysis":
            passed &= report["summary"]["total_issues"] == 2
        if fixture == "python_good":
            passed &= report["summary"]["total_issues"] == 0
        if fixture == "python_failing_tests":
            passed &= report["tests"]["status"] == "blocked"
        if fixture == "unsupported":
            passed &= any("No supported" in value for value in report["limitations"])
        results.append({"scenario": name, "passed": bool(passed), "duration_seconds": round(monotonic()-started, 4),
                        "tool_calls": report["execution"]["tool_calls"], "recoveries": report["execution"]["recoveries"]})
        sample = {0: 1, 4: 2, 6: 3}.get(len(results)-1)
        if sample:
            transcript = "\n".join(json.dumps(event) for event in events)
            (ROOT / "docs" / f"sample_run_{sample}.md").write_text(
                f"# Sample run {sample}: {name}\n\n"
                "Measured synthetic run. GitHub acquisition is replaced by a labeled fixture tool. "
                "All other tools are real; Docker execution is disabled and no LLM key is configured. "
                "This run does not demonstrate passing repository tests or a live LLM call.\n\n"
                f"## Action transcript\n\n```jsonl\n{transcript}\n```\n\n"
                f"## Final report\n\n```json\n{json.dumps(report, indent=2)}\n```\n", encoding="utf-8")
    summary = {"total_scenarios": len(results), "passed": sum(r["passed"] for r in results),
               "failed": sum(not r["passed"] for r in results),
               "recovery_success_rate": sum(r["passed"] and r["recoveries"] > 0 for r in results[-3:]) / 3,
               "average_execution_seconds": round(sum(r["duration_seconds"] for r in results)/len(results),4),
               "number_of_tool_calls": sum(r["tool_calls"] for r in results),
               "scope": "Offline synthetic integration evaluation; no Docker or live LLM claims", "scenarios": results}
    (ROOT / "docs" / "evaluation.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return summary["failed"]


if __name__ == "__main__":
    sys.exit(bool(evaluate()))
