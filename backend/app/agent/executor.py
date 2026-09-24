import time

from app.agent.recovery import RecoveryEngine
from app.agent.validator import ResultValidator
from app.models import ToolResult
from app.tools.base import ToolError


class Executor:
    def __init__(self, tools, settings, emit):
        self.tools, self.settings, self.emit = tools, settings, emit
        self.validator = ResultValidator()
        self.recovery = RecoveryEngine()

    def execute(self, action, state):
        tool = self.tools[action]
        if action not in state.tools_used:
            state.tools_used.append(action)
        for attempt in range(self.recovery.max_retries + 1):
            state.calls += 1
            self.emit("tool_started", {"tool": action, "attempt": attempt, "action": tool.description})
            try:
                if self.settings.simulate_failure and self.settings.simulated_failure_tool == action:
                    if action == "static_analysis":
                        result = {"observation": "Induced invalid result", "data": {}}
                    else:
                        raise ToolError("timeout", "Simulated tool timeout (deliberately induced)")
                else:
                    result = tool.execute(state, self.settings, tool.input_schema())
                result = self.validator.validate(action, result)
                self.emit("tool_completed", {"tool": action, "attempt": attempt,
                                             "status": result.status, "observation": result.observation})
                if attempt:
                    state.recoveries += 1
                return result
            except ToolError as exc:
                error = exc
            except Exception:
                # Never expose exception text containing request headers or source secrets.
                error = ToolError("fatal", "Unexpected internal tool failure; see server diagnostics")
            state.failures += 1
            self.emit("tool_failed", {"tool": action, "attempt": attempt, "category": error.category,
                                       "error": str(error)})
            decision = self.recovery.decide(error, attempt, action)
            self.emit("recovery_started", {"tool": action, "category": error.category, "action": decision,
                                           "observation": self.describe(decision)})
            if decision == "stop":
                raise error
            if decision == "retry":
                time.sleep(0.1 * (2 ** attempt))
                continue
            state.recoveries += 1
            state.limitations.append(f"{action}: {error}. Fallback: continue with available static evidence.")
            if action == "static_analysis":
                return ToolResult(status="skipped", observation="Static analyzer unavailable; repository inspection retained",
                                  data={"issues": [], "limitations": ["Static analysis failed; no clean-code conclusion is possible"]})
            if action == "test_runner":
                return ToolResult(status="blocked", observation="Continue with static analysis and evidence verification",
                                  data={"status": "blocked", "passed": 0, "failed": 0, "duration": 0,
                                        "error_summary": str(error)})
            return ToolResult(status="skipped", observation="Unavailable tool; continue with existing evidence")

    @staticmethod
    def describe(decision):
        return {"retry": "Retry the same bounded tool operation", "stop": "Stop and report the failure safely",
                "fallback": "Continue with available static evidence; do not bypass security policy"}[decision]

