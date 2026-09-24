from collections import Counter

from app.models import ToolResult
from app.security.paths import read_source, source_files
from app.tools.base import Tool, ToolError


class RepositoryTool(Tool):
    name = "repository"
    description = "Inspect file extensions, manifests, frameworks and test presence without imports."

    def execute(self, state, settings, arguments):
        files = list(source_files(state.root))
        names = [p.relative_to(state.root).as_posix() for p in files]
        extensions = Counter(p.suffix.lower() for p in files)
        mapping = {".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript", ".ts": "TypeScript",
                   ".tsx": "TypeScript", ".rs": "Rust", ".go": "Go", ".java": "Java"}
        languages = sorted({mapping[e] for e in extensions if e in mapping}) or ["Unknown"]
        manifest = ""
        for name in ["requirements.txt", "pyproject.toml", "package.json"]:
            if name in names:
                try:
                    manifest += read_source(state.root, name, settings.max_file_bytes).lower()
                except ToolError:
                    pass
        frameworks = [label for key, label in {"fastapi": "FastAPI", "django": "Django", "flask": "Flask",
                                               "react": "React", "next": "Next.js"}.items() if key in manifest]
        tests = [n for n in names if n.split("/")[-1].startswith("test_") and n.endswith(".py")]
        return ToolResult(observation=f"Inspected {len(files)} files; languages: {', '.join(languages)}", data={
            "languages": languages, "frameworks": frameworks, "file_count": len(files),
            "package_manager": "npm" if "package.json" in names else "pip" if "Python" in languages else None,
            "test_framework": "pytest" if tests else None, "test_files": tests,
            "has_readme": any(n.lower().startswith("readme") for n in names),
            "source_bytes": sum(p.stat().st_size for p in files)})

