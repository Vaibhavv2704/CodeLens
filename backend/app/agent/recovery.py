from app.tools.base import ToolError


class RecoveryEngine:
    max_retries = 2

    def decide(self, error: ToolError, attempt: int, tool: str) -> str:
        if error.category in {"timeout", "transient", "invalid_tool_output"} and attempt < self.max_retries:
            return "retry"
        if tool in {"github", "repository", "report"} or error.category in {"fatal", "invalid_input"}:
            return "stop"
        return "fallback"

