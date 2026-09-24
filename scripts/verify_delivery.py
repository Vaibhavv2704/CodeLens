"""Check deliverable paths and recognizable secret patterns without printing secret values."""
import argparse
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--git", default="git")
args = parser.parse_args()
result = subprocess.run([args.git, "-c", f"safe.directory={ROOT.as_posix()}", "ls-files", "--cached",
                         "--others", "--exclude-standard"], cwd=ROOT, text=True, capture_output=True, check=True)
paths = sorted(set(result.stdout.splitlines()) | {"docs/file_structure.md"})
(ROOT / "docs/file_structure.md").write_text(
    "# Complete deliverable file structure\n\nGenerated from Git-visible paths; ignores dependencies, databases, "
    "secrets and retained temporary outputs.\n\n```text\n" + "\n".join(paths) + "\n```\n", encoding="utf-8")
problems = []
for name in paths:
    path = ROOT / name
    if path.name == ".env" or any(part in {"node_modules", ".venv", ".pnpm-store"} for part in path.parts):
        problems.append(f"Unwanted deliverable: {name}")
    if path.suffix in {".png"} or not path.is_file():
        continue
    content = path.read_text(encoding="utf-8", errors="replace")
    patterns = [r"\bghp_[A-Za-z0-9]{30,}\b", r"\bgithub_pat_[A-Za-z0-9_]{30,}\b",
                r"\bsk-[A-Za-z0-9_-]{30,}\b", r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"]
    if any(re.search(pattern, content) for pattern in patterns):
        problems.append(f"Possible secret pattern: {name}")
print(f"Inspected {len(paths)} deliverable paths; {len(problems)} problems")
for problem in problems:
    print(problem)
raise SystemExit(bool(problems))
