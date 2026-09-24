from dataclasses import dataclass, field
from pathlib import Path

from app.models import Goal, Issue, Plan


@dataclass
class AgentState:
    goal: Goal
    root: Path
    plan: Plan
    repository: dict = field(default_factory=dict)
    issues: list[Issue] = field(default_factory=list)
    tests: dict = field(default_factory=dict)
    limitations: list[str] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)
    failures: int = 0
    recoveries: int = 0
    calls: int = 0
    report: dict = field(default_factory=dict)

