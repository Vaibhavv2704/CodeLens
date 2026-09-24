"""Best-effort redaction of recognizable secrets before persistence or LLM submission."""
import re

PATTERNS = [
    r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b",
    r"\bgithub_pat_[A-Za-z0-9_]{20,}\b",
    r"\bsk-[A-Za-z0-9_-]{16,}\b",
    r"\bAKIA[A-Z0-9]{16}\b",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----",
]


def redact(value):
    if isinstance(value, str):
        for pattern in PATTERNS:
            value = re.sub(pattern, "[REDACTED]", value)
        return value
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    return value
