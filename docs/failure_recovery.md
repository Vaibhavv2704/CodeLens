# Failure recovery

Each tool attempt has a `tool_started` event and either a validated `tool_completed` event or a
`tool_failed` event with a safe category. Failed attempts are persisted individually. The policy is:

| Category | Decision |
|---|---|
| timeout / transient / invalid_tool_output | Initial attempt plus at most two retries, 0.1/0.2s backoff |
| dependency_error | Fall back without installing or executing repository dependencies |
| unsupported_repository | Retain generic metadata; explain unsupported analysis |
| security_block | Never relax policy; skip optional operation or stop unsafe acquisition |
| invalid_input / fatal | Stop and emit a structured failure report |

Acquisition, inspection and report generation are essential; exhaustion stops the review. Optional
tool exhaustion degrades the step and preserves the other evidence. `completed` means the orchestration
finished, **not** that tests passed or every tool was available. Degraded steps and limitations remain
visible. A failing test is a valid test result, not an infrastructure crash to retry until it passes.

## Demonstrations

From the project root, with the virtual environment active:

```powershell
$env:SIMULATE_FAILURE = 'true'
$env:SIMULATED_FAILURE_TOOL = 'test_runner'
python scripts/review.py https://github.com/synthetic/python_bad --fixture python_bad
$env:SIMULATED_FAILURE_TOOL = 'static_analysis'
python scripts/review.py https://github.com/synthetic/python_bad --fixture python_bad
Remove-Item Env:SIMULATE_FAILURE
Remove-Item Env:SIMULATED_FAILURE_TOOL
```

The first run induces three timeouts, then falls back to existing static findings and source verification.
The second returns a malformed analyzer result, which is rejected three times; the report explicitly
states static analysis was unavailable. The security scenario in `scripts/evaluate.py` attempts a path
outside the temporary root, receives a `security_block`, and continues without that optional operation.
These are injected failures, not claims that a real Docker run timed out.

`execution.tool_failures` counts failed attempts; `recoveries` counts successful retries or fallback
decisions. The evaluation's recovery rate uses the three intentionally failed scenarios as denominator.
