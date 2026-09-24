import json

from openai import OpenAI, APIError, APITimeoutError
from pydantic import BaseModel, Field

from app.models import ToolResult
from app.prompts.reviewer_prompt import REVIEWER_PROMPT
from app.security.redaction import redact
from app.tools.base import Tool, ToolError


class Explanation(BaseModel):
    issue_index: int
    explanation: str = Field(max_length=2500)
    suggested_fix: str = Field(max_length=2500)


class ReviewAnalysis(BaseModel):
    explanations: list[Explanation]


class LLMTool(Tool):
    name = "llm_analysis"
    description = "Request structured explanations for existing findings, without granting execution authority."

    def execute(self, state, settings, arguments):
        if not settings.openai_api_key:
            return ToolResult(status="skipped", observation="LLM key not configured; deterministic findings retained")
        if not state.issues:
            return ToolResult(status="skipped", observation="No observed findings to explain")
        payload = {"objective": state.goal.objective,
                   "findings": [{"index": i, **issue.model_dump()} for i, issue in enumerate(state.issues[:20])]}
        try:
            with OpenAI(api_key=settings.openai_api_key, timeout=30, max_retries=0) as client:
                response = client.responses.parse(model=settings.llm_model, instructions=REVIEWER_PROMPT,
                                                  input=json.dumps(redact(payload)), text_format=ReviewAnalysis,
                                                  max_output_tokens=4000, store=False)
            parsed = response.output_parsed
            if parsed is None:
                raise ToolError("invalid_tool_output", "LLM refused or returned an incomplete response")
            ids = [e.issue_index for e in parsed.explanations]
            if len(ids) != len(set(ids)) or any(i < 0 or i >= min(20, len(state.issues)) for i in ids):
                raise ToolError("invalid_tool_output", "LLM returned unknown or duplicate finding IDs")
            return ToolResult(observation=f"AI explained {len(ids)} observed findings", data=parsed.model_dump())
        except APITimeoutError as exc:
            raise ToolError("timeout", "LLM request timed out") from exc
        except APIError as exc:
            raise ToolError("dependency_error", "LLM provider unavailable; deterministic findings retained") from exc
