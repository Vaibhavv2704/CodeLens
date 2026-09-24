"""Publish this reviewed project using configured Git credentials, without printing secrets."""
import argparse
import json
import os
from pathlib import Path
import subprocess

import httpx

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--git", default="git")
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
git = [args.git, "-c", f"safe.directory={ROOT.as_posix()}"]


def command(*values):
    return subprocess.run([*git, *values], cwd=ROOT, text=True, capture_output=True, env=env, timeout=90)


credential = subprocess.run([*git, "credential", "fill"], cwd=ROOT,
                            input="protocol=https\nhost=github.com\n\n", text=True,
                            capture_output=True, env=env, timeout=15)
fields = dict(line.split("=", 1) for line in credential.stdout.splitlines() if "=" in line)
token = fields.get("password")
if not token:
    raise SystemExit("No GitHub credential available; run gh auth login")
with httpx.Client(headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
                  timeout=30, follow_redirects=False) as client:
    account = client.get("https://api.github.com/user")
    if account.status_code != 200:
        raise SystemExit(f"GitHub authentication failed: HTTP {account.status_code}")
    login = account.json()["login"]
    name = "agentic-github-code-reviewer"
    target = f"https://github.com/{login}/{name}.git"
    repository = client.get(f"https://api.github.com/repos/{login}/{name}")
    if args.check:
        print(json.dumps({"account": login, "repository_exists": repository.status_code == 200,
                          "lookup_status": repository.status_code}))
        raise SystemExit(0)
    if command("status", "--porcelain").stdout.strip():
        raise SystemExit("Working tree must be clean before publication")
    if repository.status_code == 404:
        created = client.post("https://api.github.com/user/repos", json={
            "name": name, "private": True,
            "description": "Observable multi-tool GitHub code review agent with planning, validation and failure recovery"})
        if created.status_code != 201:
            raise SystemExit(f"GitHub repository creation failed: HTTP {created.status_code}")
        repository_data = created.json()
    elif repository.status_code == 200:
        repository_data = repository.json()
        existing_remote = command("remote", "get-url", "origin")
        if repository_data.get("size", 0) > 0 and existing_remote.stdout.strip() != target:
            raise SystemExit("Existing nonempty repository is not this project's origin; refusing to overwrite")
    else:
        raise SystemExit(f"GitHub repository lookup failed: HTTP {repository.status_code}")
    remote = command("remote", "get-url", "origin")
    if remote.returncode != 0:
        if command("remote", "add", "origin", target).returncode:
            raise SystemExit("Could not add remote")
    elif remote.stdout.strip() != target:
        raise SystemExit("Existing origin points elsewhere; refusing to replace it")
    pushed = command("push", "-u", "origin", "main")
    if pushed.returncode:
        raise SystemExit("Push failed; inspect Git authentication or branch protection (no force push attempted)")
    local = command("rev-parse", "HEAD").stdout.strip()
    remote_head = command("ls-remote", "origin", "refs/heads/main").stdout.split()
    if not remote_head or remote_head[0] != local:
        raise SystemExit("Could not verify remote main matches local HEAD")
    print(json.dumps({"url": repository_data["html_url"], "private": repository_data["private"],
                      "branch": "main", "commit": local, "remote_verified": True}))
