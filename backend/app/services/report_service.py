from collections import Counter

from app.models import ToolResult
from app.tools.base import Tool


class ReportTool(Tool):
    name = "report"
    description = "Compile only observed state into a structured review report."

    def execute(self, state, settings, arguments):
        counts = Counter(i.severity for i in state.issues)
        report = {
            "repository": state.repository,
            "review": {"objective": state.goal.objective, "status": "completed"},
            "summary": {"total_issues": len(state.issues), **{s: counts[s] for s in ["critical", "high", "medium", "low"]}},
            "issues": [i.model_dump() for i in state.issues],
            "tests": state.tests, "tools_used": list(state.tools_used),
            "execution": {"steps_completed": sum(s.status == "completed" for s in state.plan.steps),
                          "tool_failures": state.failures, "recoveries": state.recoveries, "tool_calls": state.calls},
            "limitations": list(dict.fromkeys(state.limitations)),
            "recommendations": list(dict.fromkeys(i.suggested_fix for i in sorted(
                state.issues, key=lambda i: {"critical": 0, "high": 1, "medium": 2, "low": 3}[i.severity])))[:10],
        }
        return ToolResult(observation="Structured report compiled from observed results", data=report)

