# Sample run 2: Deliberate test-runner timeout

Measured synthetic run. GitHub acquisition is replaced by a labeled fixture tool. All other tools are real; Docker execution is disabled and no LLM key is configured. This run does not demonstrate passing repository tests or a live LLM call.

## Action transcript

```jsonl
{"type": "plan_created", "data": {"goal": "Find important code quality, reliability and maintainability issues.", "strategy": "Inspect repository before selecting language-specific analysis.", "steps": [{"id": 1, "action": "github", "description": "Fetch a bounded snapshot and record the commit", "status": "pending"}, {"id": 2, "action": "repository", "description": "Inspect languages, frameworks and test configuration", "status": "pending"}, {"id": 3, "action": "static_analysis", "description": "Analyze source quality", "status": "pending"}, {"id": 4, "action": "test_runner", "description": "Check tests within the configured sandbox policy", "status": "pending"}, {"id": 5, "action": "source_inspection", "description": "Re-read source evidence and verify findings", "status": "pending"}, {"id": 6, "action": "llm_analysis", "description": "Request evidence-bound AI explanations, if configured", "status": "pending"}, {"id": 7, "action": "report", "description": "Compile structured findings, limitations and recovery history", "status": "pending"}]}}
{"type": "step_started", "data": {"id": 1, "action": "github", "description": "Fetch a bounded snapshot and record the commit", "status": "running"}}
{"type": "tool_started", "data": {"tool": "github", "attempt": 0, "action": "Load a labeled synthetic fixture instead of a network download"}}
{"type": "tool_completed", "data": {"tool": "github", "attempt": 0, "status": "ok", "observation": "Synthetic local fixture: python_bad; GitHub not contacted"}}
{"type": "step_completed", "data": {"id": 1, "action": "github", "description": "Fetch a bounded snapshot and record the commit", "status": "completed"}}
{"type": "step_started", "data": {"id": 2, "action": "repository", "description": "Inspect languages, frameworks and test configuration", "status": "running"}}
{"type": "tool_started", "data": {"tool": "repository", "attempt": 0, "action": "Inspect file extensions, manifests, frameworks and test presence without imports."}}
{"type": "tool_completed", "data": {"tool": "repository", "attempt": 0, "status": "ok", "observation": "Inspected 2 files; languages: Python"}}
{"type": "step_completed", "data": {"id": 2, "action": "repository", "description": "Inspect languages, frameworks and test configuration", "status": "completed"}}
{"type": "plan_updated", "data": {"goal": "Find important code quality, reliability and maintainability issues.", "strategy": "Python AST rules and isolated pytest where enabled.", "steps": [{"id": 1, "action": "github", "description": "Fetch a bounded snapshot and record the commit", "status": "completed"}, {"id": 2, "action": "repository", "description": "Inspect languages, frameworks and test configuration", "status": "completed"}, {"id": 3, "action": "static_analysis", "description": "Analyze Python AST", "status": "pending"}, {"id": 4, "action": "test_runner", "description": "Check tests within the configured sandbox policy", "status": "pending"}, {"id": 5, "action": "source_inspection", "description": "Re-read source evidence and verify findings", "status": "pending"}, {"id": 6, "action": "llm_analysis", "description": "Request evidence-bound AI explanations, if configured", "status": "pending"}, {"id": 7, "action": "report", "description": "Compile structured findings, limitations and recovery history", "status": "pending"}]}}
{"type": "step_started", "data": {"id": 3, "action": "static_analysis", "description": "Analyze Python AST", "status": "running"}}
{"type": "tool_started", "data": {"tool": "static_analysis", "attempt": 0, "action": "Analyze Python syntax trees and conservative JS patterns without executing code."}}
{"type": "tool_completed", "data": {"tool": "static_analysis", "attempt": 0, "status": "ok", "observation": "Analyzed 2 source files; 2 candidates"}}
{"type": "step_completed", "data": {"id": 3, "action": "static_analysis", "description": "Analyze Python AST", "status": "completed"}}
{"type": "step_started", "data": {"id": 4, "action": "test_runner", "description": "Check tests within the configured sandbox policy", "status": "running"}}
{"type": "tool_started", "data": {"tool": "test_runner", "attempt": 0, "action": "Run detected Python tests only in a restricted, networkless Docker container."}}
{"type": "tool_failed", "data": {"tool": "test_runner", "attempt": 0, "category": "timeout", "error": "Simulated tool timeout (deliberately induced)"}}
{"type": "recovery_started", "data": {"tool": "test_runner", "category": "timeout", "action": "retry", "observation": "Retry the same bounded tool operation"}}
{"type": "tool_started", "data": {"tool": "test_runner", "attempt": 1, "action": "Run detected Python tests only in a restricted, networkless Docker container."}}
{"type": "tool_failed", "data": {"tool": "test_runner", "attempt": 1, "category": "timeout", "error": "Simulated tool timeout (deliberately induced)"}}
{"type": "recovery_started", "data": {"tool": "test_runner", "category": "timeout", "action": "retry", "observation": "Retry the same bounded tool operation"}}
{"type": "tool_started", "data": {"tool": "test_runner", "attempt": 2, "action": "Run detected Python tests only in a restricted, networkless Docker container."}}
{"type": "tool_failed", "data": {"tool": "test_runner", "attempt": 2, "category": "timeout", "error": "Simulated tool timeout (deliberately induced)"}}
{"type": "recovery_started", "data": {"tool": "test_runner", "category": "timeout", "action": "fallback", "observation": "Continue with available static evidence; do not bypass security policy"}}
{"type": "step_completed", "data": {"id": 4, "action": "test_runner", "description": "Check tests within the configured sandbox policy", "status": "degraded"}}
{"type": "step_started", "data": {"id": 5, "action": "source_inspection", "description": "Re-read source evidence and verify findings", "status": "running"}}
{"type": "tool_started", "data": {"tool": "source_inspection", "attempt": 0, "action": "Re-read bounded source files to verify every finding's file, line and quoted evidence."}}
{"type": "tool_completed", "data": {"tool": "source_inspection", "attempt": 0, "status": "ok", "observation": "Re-read evidence for 2 findings"}}
{"type": "step_completed", "data": {"id": 5, "action": "source_inspection", "description": "Re-read source evidence and verify findings", "status": "completed"}}
{"type": "step_started", "data": {"id": 6, "action": "llm_analysis", "description": "Request evidence-bound AI explanations, if configured", "status": "running"}}
{"type": "tool_started", "data": {"tool": "llm_analysis", "attempt": 0, "action": "Request structured explanations for existing findings, without granting execution authority."}}
{"type": "tool_completed", "data": {"tool": "llm_analysis", "attempt": 0, "status": "skipped", "observation": "LLM key not configured; deterministic findings retained"}}
{"type": "step_completed", "data": {"id": 6, "action": "llm_analysis", "description": "Request evidence-bound AI explanations, if configured", "status": "degraded"}}
{"type": "step_started", "data": {"id": 7, "action": "report", "description": "Compile structured findings, limitations and recovery history", "status": "running"}}
{"type": "tool_started", "data": {"tool": "report", "attempt": 0, "action": "Compile only observed state into a structured review report."}}
{"type": "tool_completed", "data": {"tool": "report", "attempt": 0, "status": "ok", "observation": "Structured report compiled from observed results"}}
{"type": "step_completed", "data": {"id": 7, "action": "report", "description": "Compile structured findings, limitations and recovery history", "status": "completed"}}
{"type": "review_completed", "data": {"status": "completed", "summary": {"total_issues": 2, "critical": 0, "high": 1, "medium": 1, "low": 0}}}
```

## Final report

```json
{
  "repository": {
    "name": "synthetic/python_bad",
    "url": "https://github.com/synthetic/python_bad",
    "commit": "synthetic-no-git-commit",
    "fixture": true,
    "languages": [
      "Python"
    ],
    "frameworks": [],
    "file_count": 2,
    "package_manager": "pip",
    "test_framework": "pytest",
    "test_files": [
      "test_service.py"
    ],
    "has_readme": false,
    "source_bytes": 252,
    "ai_explanations": []
  },
  "review": {
    "objective": "Find important code quality, reliability and maintainability issues.",
    "status": "completed",
    "duration_seconds": 0.328
  },
  "summary": {
    "total_issues": 2,
    "critical": 0,
    "high": 1,
    "medium": 1,
    "low": 0
  },
  "issues": [
    {
      "title": "Mutable default argument",
      "severity": "high",
      "category": "correctness",
      "file": "service.py",
      "line": 1,
      "evidence": "def collect(item, values=[]):",
      "description": "Default containers are shared across calls and can retain data unexpectedly.",
      "suggested_fix": "Default to None and allocate a fresh container inside the function.",
      "confidence": 0.98,
      "provenance": "observed_by_tool",
      "verification": "verified"
    },
    {
      "title": "Broad exception handler with empty body",
      "severity": "medium",
      "category": "reliability",
      "file": "service.py",
      "line": 9,
      "evidence": "except Exception:",
      "description": "This handler catches every Exception and does nothing locally. Surrounding control flow may intentionally handle the failure; inspect that context before changing it.",
      "suggested_fix": "Consider catching specific failures; document intentional suppression or preserve error context.",
      "confidence": 0.8,
      "provenance": "observed_by_tool",
      "verification": "potential"
    }
  ],
  "tests": {
    "status": "blocked",
    "passed": 0,
    "failed": 0,
    "duration": 0,
    "error_summary": "Simulated tool timeout (deliberately induced)"
  },
  "tools_used": [
    "github",
    "repository",
    "static_analysis",
    "test_runner",
    "source_inspection",
    "llm_analysis",
    "report"
  ],
  "execution": {
    "steps_completed": 5,
    "tool_failures": 3,
    "recoveries": 1,
    "tool_calls": 9,
    "steps_degraded": 2
  },
  "limitations": [
    "test_runner: Simulated tool timeout (deliberately induced). Fallback: continue with available static evidence.",
    "Continue with static analysis and evidence verification",
    "Test coverage: Simulated tool timeout (deliberately induced)",
    "LLM key not configured; deterministic findings retained"
  ],
  "recommendations": [
    "Default to None and allocate a fresh container inside the function.",
    "Consider catching specific failures; document intentional suppression or preserve error context."
  ]
}
```
