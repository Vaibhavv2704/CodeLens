import re
import shutil
import subprocess
import time
import uuid

from app.models import TestResult
from app.security.command_policy import allowed_test_command
from app.tools.base import ToolError


def docker_command(root, image: str, name: str) -> list[str]:
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._/:@-]+", image):
        raise ToolError("security_block", "Invalid sandbox image")
    if "," in str(root.resolve()):
        raise ToolError("security_block", "Sandbox mount path contains unsupported separator")
    return ["docker", "run", "--rm", "--pull=never", "--name", name, "--network=none", "--read-only",
            "--cpus=1", "--memory=256m", "--memory-swap=256m", "--pids-limit=64", "--cap-drop=ALL",
            "--security-opt=no-new-privileges", "--user=65534:65534", "--ulimit", "nofile=256:256",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m", "--mount",
            f"type=bind,source={root.resolve()},target=/repo,readonly", "--workdir=/repo",
            "--env", "PYTHONDONTWRITEBYTECODE=1", "--env", "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1",
            image, *allowed_test_command("pytest")]


def run_tests(root, settings) -> TestResult:
    if not settings.enable_sandbox:
        return TestResult(status="blocked", error_summary="Docker execution disabled; static analysis continues.")
    if not shutil.which("docker"):
        raise ToolError("dependency_error", "Docker is unavailable; no repository code was executed")
    name = f"review-{uuid.uuid4().hex}"
    command = docker_command(root, settings.sandbox_image, name)
    started = time.monotonic()
    # A draining thread keeps subprocess output bounded even for malicious test output.
    import threading
    output = bytearray()

    def drain(pipe):
        while chunk := pipe.read(4096):
            if len(output) < 32_000:
                output.extend(chunk[:32_000 - len(output)])

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
    reader = threading.Thread(target=drain, args=(process.stdout,), daemon=True)
    reader.start()
    try:
        process.wait(timeout=45)
    except subprocess.TimeoutExpired as exc:
        process.kill()
        raise ToolError("timeout", "Sandbox test run exceeded 45 seconds") from exc
    finally:
        try:
            subprocess.run(["docker", "rm", "-f", name], timeout=10, capture_output=True, shell=False)
        except (OSError, subprocess.TimeoutExpired):
            pass
        reader.join(timeout=2)
    text = output.decode("utf-8", errors="replace")
    if process.returncode == 125:
        raise ToolError("dependency_error", "Docker daemon or prebuilt sandbox image unavailable")
    passed_match = re.findall(r"(\d+) passed", text)
    failed_match = re.findall(r"(\d+) failed", text)
    passed = int(passed_match[-1]) if passed_match else 0
    failed = int(failed_match[-1]) if failed_match else 0
    if process.returncode == 5:
        return TestResult(status="not_available", duration=time.monotonic() - started,
                          error_summary="pytest did not collect tests")
    # Do not persist raw untrusted test stdout: it may contain credentials from repository files.
    success = process.returncode == 0 and passed > 0
    return TestResult(status="passed" if success else "failed", passed=passed, failed=failed,
                      duration=time.monotonic() - started,
                      error_summary="" if success else f"pytest exited with code {process.returncode}; dependencies or tests failed")
