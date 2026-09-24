from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic

from app.agent.executor import Executor
from app.agent.planner import Planner
from app.agent.router import default_tools
from app.agent.state import AgentState
from app.models import Issue
from app.tools.base import ToolError
from app.security.redaction import redact


class Agent:
    def __init__(self, settings, tools=None):
        self.settings = settings
        self.tools = tools if tools is not None else default_tools()

    def run(self, goal, emit=lambda kind, data: None):
        started = monotonic()
        planner = Planner()
        with TemporaryDirectory(prefix="review-") as directory:
            state = AgentState(goal, Path(directory), planner.create(goal))
            emit("plan_created", state.plan.model_dump())
            executor = Executor(self.tools, self.settings, emit)
            try:
                for index in range(len(state.plan.steps)):
                    step = state.plan.steps[index]
                    step.status = "running"
                    emit("step_started", step.model_dump())
                    result = executor.execute(step.action, state)
                    self.apply_result(step.action, result, state)
                    step.status = "completed" if result.status == "ok" else "degraded"
                    emit("step_completed", step.model_dump())
                    if step.action == "repository":
                        adapted = planner.create(goal, state.repository)
                        for previous, replacement in zip(state.plan.steps, adapted.steps):
                            replacement.status = previous.status
                        state.plan = adapted
                        emit("plan_updated", state.plan.model_dump())
                report = state.report
                report["review"]["duration_seconds"] = round(monotonic() - started, 3)
                report["execution"]["steps_completed"] = sum(s.status == "completed" for s in state.plan.steps)
                report["execution"]["steps_degraded"] = sum(s.status == "degraded" for s in state.plan.steps)
                emit("review_completed", {"status": "completed", "summary": report["summary"]})
                return redact(report)
            except ToolError as exc:
                step.status = "failed"
                emit("step_completed", step.model_dump())
                report = {"repository": {"url": goal.repository_url, **state.repository},
                          "review": {"objective": goal.objective, "status": "failed",
                                     "duration_seconds": round(monotonic() - started, 3)},
                          "issues": [i.model_dump() for i in state.issues], "summary": {},
                          "tools_used": state.tools_used, "limitations": [*state.limitations, str(exc)],
                          "execution": {"tool_failures": state.failures, "recoveries": state.recoveries,
                                        "tool_calls": state.calls}, "error_category": exc.category}
                emit("review_failed", {"error": str(exc), "category": exc.category})
                return redact(report)

    @staticmethod
    def apply_result(action, result, state):
        if result.status != "ok":
            state.limitations.append(result.observation)
        if action in {"github", "repository"}:
            state.repository.update(result.data)
        elif action in {"static_analysis", "source_inspection"} and "issues" in result.data:
            state.issues = [Issue.model_validate(i) for i in result.data["issues"]]
            state.limitations.extend(result.data.get("limitations", []))
        elif action == "test_runner":
            state.tests = result.data
            if state.tests.get("status") != "passed":
                state.limitations.append(f"Test coverage: {state.tests.get('error_summary', 'Tests did not pass')}")
        elif action == "llm_analysis":
            # Explanations are separate; the model cannot overwrite evidence or observed counts.
            state.repository["ai_explanations"] = result.data.get("explanations", [])
        elif action == "report":
            state.report = result.data
