# Delivery verification

## Verified locally

- Natural-language objective and strict GitHub URL validation, explicit validated plan and state.
- Seven named tools, sequential routing, structured output validation, two retries, safe fallback.
- Python AST rules and source evidence verification, with context-sensitive findings marked potential.
- Deliberate test-runner timeout and invalid analyzer response; security rejection without bypass.
- SQLite review/step/tool-call/issue/repository/event persistence and replayable SSE.
- API endpoints, shared-token authentication, history and JSON export.
- React rendering tests, TypeScript checking, production frontend build.
- Headless Chrome dashboard/history/report navigation, desktop/mobile screenshots, no page errors
  and no horizontal overflow at a 390 px viewport in the browser smoke test.
- Live public GitHub acquisition and static review, including submission through the browser and 31
  persisted execution events, of `pallets/itsdangerous` at the SHA recorded in
  `live_review.json`. Docker tests were blocked; AI explanation was skipped without a key.
- Seven measured synthetic evaluation scenarios; see `evaluation.json` for exact counts and timings.
- Architecture Mermaid/PNG, three actual synthetic transcripts, README, one-page write-up,
  environment templates, CI, Dockerfiles, Render/Vercel configuration and deployment instructions.

## Not verified here / manual integration steps

| Integration | Why | How to verify |
|---|---|---|
| Real Docker test execution and image builds | Docker engine/CLI absent | Install Docker; follow deployment.md and run good/failing fixtures |
| PostgreSQL/Supabase persistence | No service credentials available | Set DATABASE_URL, start backend and run API/health + a review |
| Live LLM output | OPENAI_API_KEY absent | Configure a key and review a repository with findings; inspect AI analysis |
| Private GitHub repositories | No usable configured GitHub credential | Set GITHUB_TOKEN with access and review a private repository |
| Production deployment | Render/Vercel credentials absent | Follow deployment.md; check health, live events and report in production |
| GitHub publication | Authenticated Windows-user credential found; final publication checked separately | Inspect the repository URL and verified remote commit in the delivery response |

The LLM adapter is tested using a mocked structured provider response, including rejection of invalid
finding IDs. No live-model result is claimed. Docker policy and the disabled/missing-Docker paths are
tested without executing repository code on the host. The failing-test evaluation fixture is **blocked**,
not claimed to have executed. An additional mocked failed-test result verifies failure reporting semantics.

## Acceptance interpretation

The PDF's essential agent requirements are implemented and locally exercised. The expanded brief also
asks for optional infrastructure and production verification. Those are prepared but remain unverified
where services are unavailable. This project is not represented as fully deployed or as a comprehensive
production security scanner. See README limitations and docs/security.md before exposing it publicly.

## Phase checkpoints

1. Read the brief and all three PDF pages; blank workspace confirmed.
2. Created architecture and modular skeleton; imports and schemas exercised in the first test suite.
3. Added state/planner schemas; plan and URL tests passed.
4. Added bounded repository tools and AST rules; extraction/analyzer tests passed.
5. Added validation/recovery; malformed outputs and retry policy tested (21-test checkpoint).
6. Built responsive React dashboard with reports, execution, history and error states.
7. Connected REST/SSE with persistent events; API and browser navigation tested.
8. Added authored fixtures, mock-provider tests and API/security integration tests.
9. Fixed lint, TypeScript fixture typing, a GitHub redirect-port validation bug, and a rule's
   overconfident severity after live review. Backend/frontend checks re-run after changes.
10. Generated measured evaluations/transcripts, architecture image, screenshots and write-up.
11. Prepared Docker, Compose, Render, Vercel, CI and exact manual integration checks.
12. Initialized Git, checked ignore rules and secret patterns, and prepared meaningful local commits.

Each phase is reflected by the corresponding modules in docs/file_structure.md. Exact final test
counts and build results are recorded in the delivery response and generated verification-results.json.
