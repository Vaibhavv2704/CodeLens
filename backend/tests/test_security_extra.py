import io
import tarfile

import pytest

from app.config import Settings
from app.security.redaction import redact
from app.tools.base import ToolError
from app.tools.github_tool import extract_snapshot
from tests.test_core import archive


def test_expanded_size_limit(tmp_path):
    config = Settings(_env_file=None, max_file_bytes=2)
    with pytest.raises(ToolError, match="size"):
        extract_snapshot(archive("repo/file.py", b"123"), tmp_path, config)


def test_absolute_archive(tmp_path):
    with pytest.raises(ToolError, match="Absolute"):
        extract_snapshot(archive("/repo/file.py"), tmp_path, Settings(_env_file=None))


def test_duplicate_archive(tmp_path):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for name in ["repo/file.py", "repo/FILE.py"]:
            member = tarfile.TarInfo(name)
            member.size = 1
            tar.addfile(member, io.BytesIO(b"x"))
    with pytest.raises(ToolError, match="Duplicate"):
        extract_snapshot(buffer.getvalue(), tmp_path, Settings(_env_file=None))


def test_redaction():
    secret = "ghp_" + "a" * 36
    assert redact({"evidence": f"token = '{secret}'"}) == {"evidence": "token = '[REDACTED]'"}

