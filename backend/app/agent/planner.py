from app.models import Goal, Plan, Step


class Planner:
    """A constrained planner: metadata adapts strategies, never executable commands."""

    def create(self, goal: Goal, metadata: dict | None = None) -> Plan:
        languages = (metadata or {}).get("languages", [])
        strategy = "Inspect repository before selecting language-specific analysis."
        if metadata:
            strategy = ("Python AST rules and isolated pytest where enabled." if "Python" in languages
                        else "Conservative source-pattern and repository analysis; execution unsupported.")
        labels = [
            ("github", "Fetch a bounded snapshot and record the commit"),
            ("repository", "Inspect languages, frameworks and test configuration"),
            ("static_analysis", "Analyze Python AST" if "Python" in languages else "Analyze source quality"),
            ("test_runner", "Check tests within the configured sandbox policy"),
            ("source_inspection", "Re-read source evidence and verify findings"),
            ("llm_analysis", "Request evidence-bound AI explanations, if configured"),
            ("report", "Compile structured findings, limitations and recovery history"),
        ]
        return Plan(goal=goal.objective, strategy=strategy,
                    steps=[Step(id=i, action=a, description=d) for i, (a, d) in enumerate(labels, 1)])

