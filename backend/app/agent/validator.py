from pydantic import ValidationError

from app.models import Issue, TestResult, ToolResult
from app.tools.base import ToolError


class ResultValidator:
    def validate(self, tool: str, result) -> ToolResult:
        try:
            result = ToolResult.model_validate(result)
            if tool in {"static_analysis", "source_inspection"}:
                if not isinstance(result.data.get("issues"), list):
                    raise ValueError("issues list is required")
                for issue in result.data["issues"]:
                    Issue.model_validate(issue)
            if tool == "test_runner":
                TestResult.model_validate(result.data)
            if tool == "repository" and not isinstance(result.data.get("languages"), list):
                raise ValueError("repository languages are required")
            if tool == "github" and not all(k in result.data for k in ("name", "url", "commit")):
                raise ValueError("snapshot identity is required")
            if tool == "report" and not all(k in result.data for k in ("repository", "issues", "summary")):
                raise ValueError("report missing required fields")
            return result
        except (ValidationError, ValueError, TypeError) as exc:
            raise ToolError("invalid_tool_output", f"{tool} returned an invalid result") from exc

