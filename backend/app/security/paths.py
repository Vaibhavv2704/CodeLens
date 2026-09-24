from pathlib import Path, PurePosixPath
import re

from app.tools.base import ToolError

EXCLUDED = {".git", "node_modules", ".venv", "venv", "dist", "build", "__pycache__"}


def safe_path(root: Path, relative: str) -> Path:
    path = PurePosixPath(relative)
    if (not relative or path.is_absolute() or "\\" in relative or ":" in relative
            or any(p in {"..", ".", ""} or p.endswith((".", " ")) for p in relative.split("/"))
            or any(re.fullmatch(r"(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", p)
                   for p in path.parts)):
        raise ToolError("security_block", "Unsafe repository path rejected")
    target = root.joinpath(*path.parts)
    if not target.resolve().is_relative_to(root.resolve()):
        raise ToolError("security_block", "Path escapes repository")
    current = target
    while current != root:
        if current.is_symlink():
            raise ToolError("security_block", "Symbolic links are prohibited")
        current = current.parent
    return target


def read_source(root: Path, relative: str, max_bytes: int = 300_000) -> str:
    target = safe_path(root, relative)
    if target.name.startswith(".env") or target.suffix.lower() in {".pem", ".key", ".p12"}:
        raise ToolError("security_block", "Credential-like file excluded")
    if not target.is_file() or target.stat().st_size > max_bytes:
        raise ToolError("security_block", "File absent or above source size limit")
    data = target.read_bytes()
    if b"\x00" in data:
        raise ToolError("unsupported_repository", "Binary file excluded")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ToolError("unsupported_repository", "Non-UTF-8 source excluded") from exc


def source_files(root: Path):
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if not any(p in EXCLUDED for p in relative.parts) and path.is_file():
            yield safe_path(root, relative.as_posix())
