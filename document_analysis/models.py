"""Pydantic models for the Document Analysis pipeline."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    CSV = "csv"
    TXT = "txt"
    JSON = "json"
    XML = "xml"
    HTML = "html"
    PPTX = "pptx"
    UNKNOWN = "unknown"


class OutputFormat(str, Enum):
    SUMMARY = "summary"
    EXECUTIVE_SUMMARY = "executive_summary"
    REPORT = "report"
    PRESENTATION = "presentation"
    LIST = "list"
    DATABASE_ENTRY = "database_entry"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    NEW_BRIEF = "new_brief"
    COMPARISON = "comparison"
    TIMELINE = "timeline"
    CLIENT_BRIEF = "client_brief"


class EntityType(str, Enum):
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    DATE = "date"
    MONEY = "money"
    PRODUCT = "product"
    TECHNOLOGY = "technology"
    CONCEPT = "concept"
    OTHER = "other"


class ExtractedEntity(BaseModel):
    text: str
    entity_type: EntityType
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    source_document: str = ""
    context: str = ""


class DocumentInfo(BaseModel):
    file_path: str
    file_name: str
    doc_type: DocumentType
    size_bytes: int = 0
    page_count: int = 0
    word_count: int = 0
    char_count: int = 0
    language: str = "unknown"
    encoding: str = "utf-8"
    created_at: datetime | None = None
    modified_at: datetime | None = None
    extracted_at: datetime = Field(default_factory=datetime.now)
    raw_text: str = ""
    tables: list[dict[str, Any]] = Field(default_factory=list)
    entities: list[ExtractedEntity] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    summary: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class FolderStats(BaseModel):
    folder_path: str
    total_files: int = 0
    supported_files: int = 0
    unsupported_files: int = 0
    total_size_bytes: int = 0
    files_by_type: dict[str, int] = Field(default_factory=dict)
    discovered_at: datetime = Field(default_factory=datetime.now)


class CrossReference(BaseModel):
    entity_a: str
    entity_b: str
    relationship_type: str
    strength: float = Field(ge=0.0, le=1.0, default=0.5)
    source_documents: list[str] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    date: str
    description: str
    source_document: str = ""
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)


class FolderAnalysis(BaseModel):
    folder_path: str
    stats: FolderStats
    documents: list[DocumentInfo] = Field(default_factory=list)
    cross_themes: list[str] = Field(default_factory=list)
    relationships: list[CrossReference] = Field(default_factory=list)
    timeline: list[TimelineEvent] = Field(default_factory=list)
    narrative: str = ""
    gaps: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    analyzed_at: datetime = Field(default_factory=datetime.now)
    processing_errors: list[str] = Field(default_factory=list)


class AnalysisOutput(BaseModel):
    title: str
    output_format: OutputFormat
    content: str
    structured_data: dict[str, Any] = Field(default_factory=dict)
    source_analysis: FolderAnalysis | None = None
    generated_at: datetime = Field(default_factory=datetime.now)
    word_count: int = 0
    ai_enhanced: bool = False
