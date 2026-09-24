"""Persist three labeled, measured fixture runs for the local dashboard's history page."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.agent.agent import Agent  # noqa: E402
from app.config import Settings  # noqa: E402
from app.models import Goal  # noqa: E402
from app.services.database import Store  # noqa: E402
from tests.helpers import fixture_tools  # noqa: E402

settings = Settings()
store = Store(settings.database_url)
# Create schema without marking an active server's jobs interrupted.
from app.services.database import Base  # noqa: E402
Base.metadata.create_all(store.engine)
for fixture, failure in [("python_good", False), ("python_bad", False), ("python_bad", True)]:
    config = settings.model_copy(update={"simulate_failure": failure, "simulated_failure_tool": "test_runner",
                                         "enable_sandbox": False, "openai_api_key": ""})
    goal = Goal(repository_url=f"https://github.com/synthetic/{fixture}",
                objective="SYNTHETIC DEMO: " + ("Demonstrate timeout recovery" if failure else "Review authored fixture"))
    identifier = store.create(goal)
    report = Agent(config, fixture_tools(fixture)).run(goal, lambda kind, data: store.emit(identifier, kind, data))
    store.finish(identifier, report)
    print(f"{fixture} failure={failure}: {identifier}")
