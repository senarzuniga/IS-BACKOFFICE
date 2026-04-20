"""Base canonical model with strict IDs and lineage."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class SourceTrace(BaseModel):
    """Records the provenance of any data point."""
    source_id: str = Field(default_factory=_uuid)
    source_type: str  # email | pdf | word | excel | txt | folder | crm | manual
    file_path: Optional[str] = None
    checksum: Optional[str] = None  # SHA-256 of raw content
    ingested_at: datetime = Field(default_factory=_now)
    client_ref: Optional[str] = None  # detected client reference
    document_class: Optional[str] = None  # offer | contract | report | invoice | other
    raw_snippet: Optional[str] = None  # first 500 chars of raw content

    model_config = {"extra": "forbid"}


class BaseEntity(BaseModel):
    """All canonical entities inherit from this."""
    id: str = Field(default_factory=_uuid)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    source_trace_ids: List[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    needs_review: bool = False

    model_config = {"extra": "forbid"}
