import re

from app.models import Issue


def analyze_javascript(file: str, source: str) -> list[Issue]:
    """Conservative lexical candidates, intentionally not advertised as ESLint/AST."""
    issues = []
    for number, line in enumerate(source.splitlines(), 1):
        if re.match(r"^\s*debugger\s*;?\s*$", line):
            issues.append(Issue(title="Debugger statement", severity="low", category="code smells", file=file,
                                line=number, evidence=line.strip(), description="A debugger statement remains in source.",
                                suggested_fix="Remove the statement if it is not intentional.", confidence=0.8))
    return issues

