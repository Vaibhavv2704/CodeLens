# Architecture

```mermaid
flowchart TD
    User --> React[React + TypeScript dashboard]
    React --> API[FastAPI REST + replayable SSE]
    API --> Queue[Bounded in-process job executor]
    Queue --> Agent[Agent orchestrator + explicit state]
    Agent --> Planner[Validated adaptive planner]
    Planner --> Router[Allowlisted tool router]
    Router --> GitHub[Bounded GitHub snapshot]
    Router --> Inspector[Repository inspector]
    Router --> Static[Python AST + conservative JS rules]
    Router --> Tests[Opt-in Docker pytest runner]
    Router --> Source[Evidence verification]
    Router --> LLM[Optional structured LLM analysis]
    GitHub & Inspector & Static & Tests & Source & LLM --> Validator[Result validator]
    Validator --> Recovery[Category-based retry or fallback]
    Recovery --> Router
    Validator --> Report[Structured report]
    Agent --> DB[(SQLAlchemy / PostgreSQL)]
    Report --> DB
    DB --> React
```

Events are public action summaries, never hidden reasoning. Database commits precede SSE delivery.
Each job owns a temporary snapshot. Plans adapt after repository inspection, using fixed tool names.
The LLM can explain observed evidence but cannot change tools, counts, commands or execution status.
Local SQLite is a zero-service convenience; deployment uses PostgreSQL. One API process owns the
bounded executor; interrupted reviews are marked failed on restart rather than silently resumed.
