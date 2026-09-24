from app.models import ToolResult
from app.security.paths import read_source
from app.tools.base import Tool, ToolError


def verify_issue(root, issue, limit):
    try:
        lines = read_source(root, issue.file, limit).splitlines()
        return 0 < issue.line <= len(lines) and issue.evidence.strip() == lines[issue.line - 1].strip()[:1500]
    except ToolError:
        return False


class SourceInspectionTool(Tool):
    name = "source_inspection"
    description = "Re-read bounded source files to verify every finding's file, line and quoted evidence."

    def execute(self, state, settings, arguments):
        issues = []
        for issue in state.issues:
            verified = verify_issue(state.root, issue, settings.max_file_bytes)
            # A lexical JS match verifies a quote, not language semantics.
            semantic = issue.file.endswith(".py") and issue.title not in {
                "Dynamic eval requires input validation", "Broad exception handler with empty body"}
            issues.append(issue.model_copy(update={"verification": "verified" if verified and semantic else "potential"}))
        return ToolResult(observation=f"Re-read evidence for {len(issues)} findings",
                          data={"issues": [i.model_dump() for i in issues]})
