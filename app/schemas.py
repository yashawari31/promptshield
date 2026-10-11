from typing import Literal
from pydantic import BaseModel, Field


Source = Literal["user", "voice_transcript", "tool_output", "document"]


class ScreenRequest(BaseModel):
    text: str = Field(min_length=1, max_length=50000)
    source: Source = "user"


class ScreenResponse(BaseModel):
    request_id: str
    decision: Literal["allow", "sanitize", "block"]
    reason: str
    risk_score: float | None
    signals: list[dict]
    sanitized_text: str | None
