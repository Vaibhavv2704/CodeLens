from app.analyzers.javascript_analyzer import analyze_javascript
from app.analyzers.python_analyzer import analyze_python
from app.models import ToolResult
from app.security.paths import read_source, source_files
from app.tools.base import Tool, ToolError


class StaticAnalysisTool(Tool):
    name = "static_analysis"
    description = "Analyze Python syntax trees and conservative JS patterns without executing code."

    def execute(self, state, settings, arguments):
        issues, skipped = [], []
        analyzed = total = 0
        for path in source_files(state.root):
            if path.suffix not in {".py", ".js", ".jsx", ".ts", ".tsx"}:
                continue
            relative = path.relative_to(state.root).as_posix()
            try:
                source = read_source(state.root, relative, settings.max_file_bytes)
                total += len(source.encode())
                if total > 5_000_000:
                    skipped.append("Remaining source exceeds 5 MB analysis budget")
                    break
                analyzer = analyze_python if path.suffix == ".py" else analyze_javascript
                issues.extend(analyzer(relative, source))
                analyzed += 1
                if len(issues) >= 200:
                    skipped.append("Finding limit reached; remaining files not analyzed")
                    break
            except ToolError as exc:
                skipped.append(f"{relative}: {exc}")
        if analyzed == 0:
            skipped.append("No supported Python/JavaScript source; repository inspection only")
        return ToolResult(observation=f"Analyzed {analyzed} source files; {len(issues[:200])} candidates",
                          data={"issues": [i.model_dump() for i in issues[:200]], "analyzed_files": analyzed,
                                "limitations": skipped})

