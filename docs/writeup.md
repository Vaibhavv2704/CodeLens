# Autonomous GitHub Code Review Agent

**Problem.** A repository URL is easy to submit but useful reviews require acquisition, language
detection, evidence, and honest handling of unavailable tools. I chose the assessment's GitHub-review
example and built a bounded agent that makes those operations visible.

**Approach and architecture.** A React/TypeScript dashboard submits a natural-language objective to
FastAPI. A worker creates explicit state and a validated seven-step plan before acting. After metadata
inspection, the planner adapts its strategy to the detected languages. A router invokes typed tools;
SQLAlchemy persists job state, actions and results. Replayable SSE shows public action summaries.

**Tool orchestration.** The GitHub tool fetches a commit-pinned snapshot. Repository inspection selects
Python AST analysis or conservative JavaScript patterns. Optional pytest runs only in Docker. A source
tool re-reads evidence. Optional structured LLM output explains existing findings but cannot fabricate
tool results or run commands. The final tool compiles counts, evidence, provenance and limitations.

**Recovery.** Result validation detects malformed outputs and inconsistent test results. Transient
failures receive two retries; unavailable optional tools fall back to remaining evidence. Essential
acquisition failures terminate safely. Two deliberate failure modes and a blocked traversal operation
are evaluated and recorded as real transcripts. Valid failing tests are reported, not retried as crashes.

**Security decisions.** No repository code executes on the host. Bounded extraction rejects traversal,
links and special files. Sandbox tests are opt-in, networkless, resource-limited and read-only, without
host credentials. The model sees redacted, limited evidence and has no shell authority. Default hosting
uses static analysis because a Docker socket in a web container would undermine that separation.

**Limitations.** This is a single-user demo with a constrained, rules-based planner and in-process queue,
not an open-ended autonomous coding system. Rule coverage is deliberately small, findings need human
judgment, and evidence verification does not establish exploitability. Python tests needing dependencies
may fail in the minimal image. JavaScript test execution is unsupported. LLM calls need a configured key.
Synthetic acquisition and mocked provider tests are labeled; Docker/live-model verification is separate.

**With more time.** Add a durable queue with cancellation, per-user authorization, migrations/retention,
isolated microVM workers, calibrated multi-language rules, repository-specific trusted dependency images,
and precision/recall evaluation on independently labeled repositories.
