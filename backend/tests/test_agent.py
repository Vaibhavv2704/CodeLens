import time

import pytest
from fastapi.testclient import TestClient

from app.agent.agent import Agent
from app.config import Settings
from app.main import create_app
from app.models import Goal, ToolResult
from app.tools.base import ToolError
from tests.helpers import fixture_tools


def settings(**kwargs):
    return Settings(_env_file=None, openai_api_key="", enable_sandbox=False, **kwargs)


def test_end_to_end():
    events = []
    report = Agent(settings(), fixture_tools()).run(Goal(repository_url="https://github.com/synthetic/bad"),
                                                   lambda kind, data: events.append((kind, data)))
    assert report["review"]["status"] == "completed"
    assert report["summary"]["high"] == 1
    assert report["summary"]["medium"] == 1
    assert report["issues"][0]["verification"] == "verified"
    assert len(report["tools_used"]) == 7
    assert report["tests"]["status"] == "blocked"
    assert events[0][0] == "plan_created"
    assert events[-1][0] == "review_completed"
    assert any(kind == "plan_updated" for kind, _ in events)


@pytest.mark.parametrize("tool,category", [("test_runner", "timeout"), ("static_analysis", "invalid_tool_output")])
def test_deliberate_failures(tool, category):
    events = []
    report = Agent(settings(simulate_failure=True, simulated_failure_tool=tool), fixture_tools()).run(
        Goal(repository_url="https://github.com/synthetic/failure"), lambda kind, data: events.append((kind, data)))
    failed = [d for k, d in events if k == "tool_failed"]
    assert len(failed) == 3
    assert all(f["category"] == category for f in failed)
    assert report["execution"]["recoveries"] == 1
    assert report["review"]["status"] == "completed"
    assert any(d["action"] == "fallback" for k, d in events if k == "recovery_started")


def test_retry_then_success():
    tools = fixture_tools()
    original = tools["static_analysis"].execute
    attempts = []

    def flaky(*args):
        attempts.append(1)
        if len(attempts) == 1:
            raise ToolError("transient", "temporary failure")
        return original(*args)

    tools["static_analysis"].execute = flaky
    report = Agent(settings(), tools).run(Goal(repository_url="https://github.com/synthetic/flaky"))
    assert len(attempts) == 2
    assert report["execution"]["recoveries"] == 1
    assert len(report["issues"]) == 2


def test_fatal_acquisition():
    tools = fixture_tools()

    def reject(*args):
        raise ToolError("security_block", "Archive contains a link")

    tools["github"].execute = reject
    report = Agent(settings(), tools).run(Goal(repository_url="https://github.com/synthetic/unsafe"))
    assert report["review"]["status"] == "failed"
    assert report["error_category"] == "security_block"
    assert report["tools_used"] == ["github"]


def test_unsupported_repository():
    report = Agent(settings(), fixture_tools("unsupported")).run(Goal(repository_url="https://github.com/synthetic/rust"))
    assert report["review"]["status"] == "completed"
    assert any("No supported" in limitation for limitation in report["limitations"])
    assert report["tests"]["status"] == "not_available"


def test_test_failure_is_not_tool_crash():
    tools = fixture_tools("python_failing_tests")
    tools["test_runner"].execute = lambda *a: ToolResult(observation="Mocked failed pytest result", data={
        "status": "failed", "passed": 0, "failed": 1, "duration": 0.1, "error_summary": "Synthetic assertion failure"})
    report = Agent(settings(), tools).run(Goal(repository_url="https://github.com/synthetic/failing"))
    assert report["tests"]["failed"] == 1
    assert report["execution"]["tool_failures"] == 0


def test_api_persistence_and_sse(tmp_path):
    app = create_app(settings(database_url=f"sqlite:///{tmp_path / 'test.db'}"),
                     agent_factory=lambda cfg: Agent(cfg, fixture_tools()))
    with TestClient(app) as client:
        assert client.get("/api/health").json() == {"status": "healthy"}
        assert client.post("/api/reviews", json={"repository_url": "http://evil.com/x"}).status_code == 422
        response = client.post("/api/reviews", json={"repository_url": "https://github.com/synthetic/bad"})
        assert response.status_code == 202
        identifier = response.json()["id"]
        for _ in range(100):
            data = client.get(f"/api/reviews/{identifier}").json()
            if data["status"] in {"completed", "failed"}:
                break
            time.sleep(0.03)
        assert data["status"] == "completed"
        assert len(client.get("/api/reviews").json()) == 1
        assert client.get(f"/api/reviews/{identifier}/report").json()["summary"]["high"] == 1
        stream = client.get(f"/api/reviews/{identifier}/events").text
        assert 'plan_created' in stream and 'review_completed' in stream
        last = data["events"][-1]["id"]
        assert 'plan_created' not in client.get(f"/api/reviews/{identifier}/events?after={last}").text
        assert client.get("/api/reviews/missing").status_code == 404


def test_api_auth(tmp_path):
    app = create_app(settings(database_url=f"sqlite:///{tmp_path / 'auth.db'}", api_token="test-only-token"))
    with TestClient(app) as client:
        assert client.get("/api/reviews").status_code == 401
        assert client.get("/api/reviews", headers={"Authorization": "Bearer test-only-token"}).status_code == 200


def test_interrupted_job_is_marked_failed(tmp_path):
    from app.services.database import Store
    store = Store(f"sqlite:///{tmp_path / 'restart.db'}")
    store.initialize()
    identifier = store.create(Goal(repository_url="https://github.com/synthetic/restart"))
    store.initialize()
    assert store.get(identifier)["status"] == "failed"
    assert store.events(identifier)[-1]["type"] == "review_failed"


def test_queue_backpressure(tmp_path):
    app = create_app(settings(database_url=f"sqlite:///{tmp_path / 'queue.db'}", max_workers=1, max_queued=1))
    with TestClient(app) as client:
        app.state.capacity.acquire()
        app.state.capacity.acquire()
        response = client.post("/api/reviews", json={"repository_url": "https://github.com/synthetic/bad"})
        assert response.status_code == 429
        app.state.capacity.release()
        app.state.capacity.release()
