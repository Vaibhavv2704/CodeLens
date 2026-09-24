import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Goal(StrictModel):
    repository_url: str
    objective: str = Field(default="Find important code quality, reliability and maintainability issues.",
                           min_length=3, max_length=1500)

    @field_validator("repository_url")
    @classmethod
    def github_url(cls, value: str) -> str:
        value = value.strip().removesuffix("/").removesuffix(".git")
        if not re.fullmatch(r"https://github\.com/[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/[A-Za-z0-9_.-]{1,100}", value):
            raise ValueError("Use https://github.com/owner/repository with no query, credentials or branch path")
        if value.rsplit("/", 1)[-1] in {".", ".."}:
            raise ValueError("Invalid repository name")
        return value


Action = Literal["github", "repository", "static_analysis", "test_runner", "source_inspection",
                 "llm_analysis", "report"]


class Step(StrictModel):
    id: int = Field(ge=1)
    action: Action
    description: str
    status: Literal["pending", "running", "completed", "degraded", "failed"] = "pending"


class Plan(StrictModel):
    goal: str
    strategy: str
    steps: list[Step] = Field(min_length=2, max_length=12)

    @model_validator(mode="after")
    def validate_order(self):
        actions = [s.action for s in self.steps]
        if [s.id for s in self.steps] != list(range(1, len(self.steps) + 1)):
            raise ValueError("Step IDs must be contiguous")
        if actions[:2] != ["github", "repository"] or actions[-1] != "report":
            raise ValueError("Acquisition and inspection must precede analysis; report must be last")
        if len(set(actions)) != len(actions):
            raise ValueError("Duplicate actions")
        return self


class Issue(StrictModel):
    title: str = Field(min_length=1, max_length=180)
    severity: Literal["low", "medium", "high", "critical"]
    category: str = Field(max_length=60)
    file: str = Field(max_length=500)
    line: int = Field(ge=1)
    evidence: str = Field(min_length=1, max_length=1500)
    description: str = Field(max_length=2500)
    suggested_fix: str = Field(max_length=2500)
    confidence: float = Field(ge=0, le=1)
    provenance: Literal["observed_by_tool", "ai_analysis"] = "observed_by_tool"
    verification: Literal["verified", "potential"] = "potential"


class TestResult(StrictModel):
    status: Literal["passed", "failed", "not_available", "blocked"]
    passed: int = Field(default=0, ge=0)
    failed: int = Field(default=0, ge=0)
    duration: float = Field(default=0, ge=0)
    error_summary: str = ""

    @model_validator(mode="after")
    def consistent(self):
        if self.status == "passed" and (self.failed or self.passed == 0):
            raise ValueError("A passing run requires passed tests and no failures")
        if self.status == "failed" and not self.failed and not self.error_summary:
            raise ValueError("Failure requires failed tests or an execution error")
        if self.status in {"blocked", "not_available"} and (self.passed or self.failed):
            raise ValueError("Unexecuted tests cannot have counts")
        return self


class ToolResult(StrictModel):
    status: Literal["ok", "blocked", "skipped"] = "ok"
    observation: str
    data: dict = Field(default_factory=dict)

