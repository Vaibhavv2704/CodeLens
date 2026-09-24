from pathlib import Path
import shutil

from app.agent.router import default_tools
from app.models import ToolResult
from app.tools.base import Tool

FIXTURES = Path(__file__).parent / "fixtures"


class FixtureGitHub(Tool):
    """Explicit test double: copies synthetic authored files; never pretends to contact GitHub."""
    name = "github"
    description = "Load a labeled synthetic fixture instead of a network download"

    def __init__(self, fixture):
        self.fixture = fixture

    def execute(self, state, settings, arguments):
        shutil.copytree(FIXTURES / self.fixture, state.root, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
        return ToolResult(observation=f"Synthetic local fixture: {self.fixture}; GitHub not contacted", data={
            "name": f"synthetic/{self.fixture}", "url": state.goal.repository_url,
            "commit": "synthetic-no-git-commit", "fixture": True})


def fixture_tools(name="python_bad"):
    tools = default_tools()
    tools["github"] = FixtureGitHub(name)
    return tools
