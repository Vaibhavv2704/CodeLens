from app.tools.base import ToolError


def allowed_test_command(framework: str) -> list[str]:
    if framework != "pytest":
        raise ToolError("security_block", "Only the predefined pytest command is permitted")
    return ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--override-ini", "addopts="]

