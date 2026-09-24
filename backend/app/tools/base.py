from abc import ABC, abstractmethod

from app.models import ToolResult
from app.models.schemas import StrictModel


class ToolInput(StrictModel):
    """Tools receive trusted orchestration context separately from public arguments."""


class ToolError(Exception):
    def __init__(self, category: str, message: str):
        super().__init__(message)
        self.category = category


class Tool(ABC):
    name: str
    description: str
    input_schema = ToolInput
    output_schema = ToolResult

    @abstractmethod
    def execute(self, state, settings, arguments: ToolInput) -> ToolResult:
        """Execute a predefined operation; never accept shell text."""

