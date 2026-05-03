from __future__ import annotations

from pydantic import BaseModel, Field


class RunCycleRequest(BaseModel):
    source_type: str = Field(default="txt")
    source_id: str = Field(default="api-001")
    content: str
    classification: str | None = None
    proactive_mode: bool = True
    autolearning_mode: bool = True
    strict_mode: bool = False


class RunCycleResponse(BaseModel):
    status: str
    result: dict


class AgentRunResponse(BaseModel):
    status: str
    pipeline: list[str]
    result: dict
    alerts: list[str]
