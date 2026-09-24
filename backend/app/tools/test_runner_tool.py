from app.models import TestResult, ToolResult
from app.security.sandbox import run_tests
from app.tools.base import Tool


class TestRunnerTool(Tool):
    name = "test_runner"
    description = "Run detected Python tests only in a restricted, networkless Docker container."

    def execute(self, state, settings, arguments):
        if not state.repository.get("test_files"):
            result = TestResult(status="not_available", error_summary="No supported Python tests detected")
        else:
            result = run_tests(state.root, settings)
        return ToolResult(status="blocked" if result.status == "blocked" else "ok",
                          observation=f"Tests: {result.status}. {result.error_summary}", data=result.model_dump())

