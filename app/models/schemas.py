from typing import Any

from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)


class ResearchResponse(BaseModel):
    session_id: str


class SessionSummary(BaseModel):
    session_id: str
    query: str
    created_at: str
    status: str


class WSEvent(BaseModel):
    event: str
    session_id: str
    timestamp: str
    agent: str
    subtopic: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
