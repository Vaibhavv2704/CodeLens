import ast

from app.models import Issue


def analyze_python(file: str, source: str) -> list[Issue]:
    lines = source.splitlines()
    issues = []

    def add(node, title, severity, category, explanation, fix, confidence=0.98):
        line = node.lineno
        issues.append(Issue(title=title, severity=severity, category=category, file=file, line=line,
                            evidence=lines[line - 1].strip()[:1500], description=explanation,
                            suggested_fix=fix, confidence=confidence))

    try:
        tree = ast.parse(source, filename=file)
    except (SyntaxError, RecursionError, ValueError) as exc:
        line = max(1, min(getattr(exc, "lineno", 1) or 1, len(lines)))
        if lines:
            issues.append(Issue(title="Source could not be parsed", severity="high", category="correctness",
                                file=file, line=line, evidence=lines[line - 1].strip() or "(blank line)",
                                description="Python parser rejected this file; check syntax and Python version.",
                                suggested_fix="Check syntax using the repository's intended Python version.",
                                confidence=0.9))
        return issues
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defaults = [*node.args.defaults, *node.args.kw_defaults]
            if any(isinstance(d, (ast.List, ast.Dict, ast.Set)) for d in defaults):
                add(node, "Mutable default argument", "high", "correctness",
                    "Default containers are shared across calls and can retain data unexpectedly.",
                    "Default to None and allocate a fresh container inside the function.")
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            add(node, "Bare exception handler", "medium", "reliability",
                "A bare except also catches KeyboardInterrupt and SystemExit.",
                "Catch the specific expected exception and preserve useful error context.")
        if isinstance(node, ast.ExceptHandler) and isinstance(node.type, ast.Name) and node.type.id == "Exception":
            if all(isinstance(n, ast.Pass) for n in node.body):
                add(node, "Broad exception handler with empty body", "medium", "reliability",
                    "This handler catches every Exception and does nothing locally. Surrounding control flow may intentionally handle the failure; inspect that context before changing it.",
                    "Consider catching specific failures; document intentional suppression or preserve error context.", 0.8)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "eval":
            add(node, "Dynamic eval requires input validation", "medium", "security",
                "This call evaluates Python expressions. Exploitability depends on the provenance of its input.",
                "Prefer an explicit parser or ast.literal_eval for literal data.", 0.85)
    return issues
