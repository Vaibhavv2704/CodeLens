import io
import re
import tarfile
import time
from urllib.parse import quote

import httpx

from app.models import ToolResult
from app.security.paths import EXCLUDED, safe_path
from app.tools.base import Tool, ToolError


def extract_snapshot(data: bytes, root, settings) -> None:
    """Stream members rather than trusting tar extract or its declared total size."""
    total = count = 0
    seen = set()
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r|gz") as archive:
            for member in archive:
                if member.name.startswith("/") or "\\" in member.name:
                    raise ToolError("security_block", "Absolute archive path rejected")
                count += 1
                if count > settings.max_files:
                    raise ToolError("security_block", "Repository exceeds file count limit")
                parts = member.name.split("/")
                if len(parts) < 2:
                    continue
                relative = "/".join(parts[1:]).rstrip("/")
                if not relative:
                    continue
                target = safe_path(root, relative)
                if not (member.isfile() or member.isdir()):
                    raise ToolError("security_block", "Archive links and special files are prohibited")
                if member.isdir():
                    continue
                total += member.size
                if member.size > settings.max_file_bytes or total > settings.max_repository_bytes:
                    raise ToolError("security_block", "Expanded repository exceeds size policy")
                key = relative.casefold()
                if key in seen:
                    raise ToolError("security_block", "Duplicate archive path")
                seen.add(key)
                if any(p in EXCLUDED for p in parts) or target.name.startswith(".env"):
                    continue
                stream = archive.extractfile(member)
                if stream is None:
                    raise ToolError("invalid_tool_output", "Archive member has no data")
                content = stream.read(settings.max_file_bytes + 1)
                if len(content) != member.size:
                    raise ToolError("security_block", "Archive size mismatch")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
    except (tarfile.TarError, EOFError, OSError) as exc:
        raise ToolError("invalid_tool_output", "Invalid GitHub archive") from exc


class GitHubTool(Tool):
    name = "github"
    description = "Fetch metadata and a commit-pinned bounded GitHub tarball; never execute hooks."

    def execute(self, state, settings, arguments):
        slug = state.goal.repository_url.removeprefix("https://github.com/")
        headers = {"Accept": "application/vnd.github+json"}
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"
        try:
            with httpx.Client(timeout=20, follow_redirects=False, trust_env=False) as client:
                response = client.get(f"https://api.github.com/repos/{slug}", headers=headers)
                response.raise_for_status()
                metadata = response.json()
                branch = metadata["default_branch"]
                commit_response = client.get(f"https://api.github.com/repos/{slug}/commits/{quote(branch, safe='')}",
                                             headers=headers)
                commit_response.raise_for_status()
                commit = commit_response.json()["sha"]
                if not re.fullmatch(r"[0-9a-f]{40}", commit):
                    raise ToolError("invalid_tool_output", "Invalid commit identifier")
                # Credential headers go only to api.github.com. GitHub controls the redirect.
                archive_response = client.get(f"https://api.github.com/repos/{slug}/tarball/{commit}",
                                              headers=headers)
                if archive_response.status_code not in {301, 302, 307}:
                    archive_response.raise_for_status()
                    raise ToolError("invalid_tool_output", "Expected a GitHub archive redirect")
                location = httpx.URL(archive_response.headers["location"])
                if location.scheme != "https" or location.host != "codeload.github.com" or location.port not in {None, 443}:
                    raise ToolError("security_block", "Archive redirect destination rejected")
                started = time.monotonic()
                archive = bytearray()
                with client.stream("GET", location) as stream:
                    stream.raise_for_status()
                    for chunk in stream.iter_bytes(65536):
                        archive.extend(chunk)
                        if len(archive) > settings.max_archive_bytes:
                            raise ToolError("security_block", "Compressed archive exceeds size policy")
                        if time.monotonic() - started > 45:
                            raise ToolError("timeout", "Archive download exceeded deadline")
                extract_snapshot(bytes(archive), state.root, settings)
                return ToolResult(observation=f"Fetched {slug} at {commit[:12]}", data={
                    "name": slug, "url": state.goal.repository_url, "commit": commit, "branch": branch})
        except httpx.TimeoutException as exc:
            raise ToolError("timeout", "GitHub request timed out") from exc
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            category = "transient" if code in {429, 500, 502, 503, 504} else "invalid_input"
            raise ToolError(category, f"GitHub returned HTTP {code}; check repository access or rate limits") from exc
        except httpx.RequestError as exc:
            raise ToolError("transient", "GitHub connection failed") from exc
        except (KeyError, ValueError) as exc:
            raise ToolError("invalid_tool_output", "GitHub response missing required metadata") from exc
