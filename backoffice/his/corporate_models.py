from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


DocumentLanguage = Literal["en", "es"]
PublicationFormat = Literal["html", "pdf", "docx", "xlsx", "pptx"]
DocumentStatus = Literal["draft", "validating", "ready", "stale", "published", "failed"]


def _now() -> datetime:
    return datetime.now(UTC)


class SourceDependency(BaseModel):
    repository_id: str
    relative_path: str
    sha256: str
    size_bytes: int
    modified_at: datetime
    adapter: str
    media_type: str | None = None


class ValidationResult(BaseModel):
    check: str
    passed: bool
    severity: Literal["info", "warning", "error"] = "error"
    message: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeliveryPolicy(BaseModel):
    profile_id: str = "standard"
    allowed_formats: list[PublicationFormat] = Field(default_factory=lambda: ["html", "pdf", "docx"])
    required_languages: list[DocumentLanguage] = Field(default_factory=lambda: ["en", "es"])
    page_size: Literal["A4", "Letter"] = "A4"
    include_sources: bool = False
    include_editable_files: bool = False


class PublicationArtifact(BaseModel):
    language: DocumentLanguage
    format: PublicationFormat
    path: str
    sha256: str
    size_bytes: int


class CorporateDocument(BaseModel):
    document_id: str = Field(default_factory=lambda: uuid4().hex)
    title: str
    client: str
    project: str
    version: str = "1.0.0"
    source_language: DocumentLanguage
    languages: list[DocumentLanguage] = Field(default_factory=lambda: ["en", "es"])
    source_document_model: str
    destination: str
    visual_profile: str = "pcg_corporate"
    delivery_policy: DeliveryPolicy = Field(default_factory=DeliveryPolicy)
    dependencies: list[SourceDependency] = Field(default_factory=list)
    artifacts: list[PublicationArtifact] = Field(default_factory=list)
    validation: list[ValidationResult] = Field(default_factory=list)
    status: DocumentStatus = "draft"
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
