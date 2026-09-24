"""CLI: python scripts/review.py URL [--objective TEXT] [--fixture python_bad]."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.agent.agent import Agent  # noqa: E402
from app.config import Settings  # noqa: E402
from app.models import Goal  # noqa: E402

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("url")
parser.add_argument("--objective", default="Find important code quality and reliability issues.")
parser.add_argument("--fixture", choices=["python_good", "python_bad", "python_failing_tests", "unsupported"])
parser.add_argument("--output", type=Path)
args = parser.parse_args()
tools = None
if args.fixture:
    from tests.helpers import fixture_tools
    tools = fixture_tools(args.fixture)
report = Agent(Settings(), tools).run(Goal(repository_url=args.url, objective=args.objective),
                                     lambda kind, data: print(json.dumps({"type": kind, "data": data}), file=sys.stderr))
serialized = json.dumps(report, indent=2)
if args.output:
    args.output.write_text(serialized, encoding="utf-8")
print(serialized)
sys.exit(0 if report["review"]["status"] == "completed" else 1)
