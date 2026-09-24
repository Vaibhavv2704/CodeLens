"""Check only the configured GitHub git credential, never print or persist its secret."""
import os
import subprocess
import sys

env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
try:
    result = subprocess.run([sys.argv[1], "-c", f"safe.directory={os.getcwd()}", "credential", "fill"], input="protocol=https\nhost=github.com\n\n",
                            text=True, capture_output=True, env=env, timeout=15)
    values = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    print("GitHub credential configured: " + str(bool(values.get("password"))))
except (OSError, subprocess.TimeoutExpired):
    print("GitHub credential configured: False (helper unavailable or timed out)")
