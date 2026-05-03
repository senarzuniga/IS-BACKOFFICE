from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class InstructionIntent(str, Enum):
    EXPLORE_FOLDER = "explore_folder"
    EXTRACT_INFO = "extract_info"
    ANALYZE_DOCUMENTS = "analyze_documents"
    GENERATE_OUTPUT = "generate_output"
    COMPARE_DOCUMENTS = "compare_documents"
    FIND_SPECIFIC = "find_specific"
    STRUCTURE_DATA = "structure_data"
    CREATE_REPORT = "create_report"
    CREATE_PRESENTATION = "create_presentation"
    SUMMARIZE = "summarize"
    CUSTOM = "custom"


class OutputType(str, Enum):
    LIST = "list"
    TABLE = "table"
    SUMMARY = "summary"
    EXECUTIVE_SUMMARY = "executive_summary"
    REPORT = "report"
    PRESENTATION = "presentation"
    TIMELINE = "timeline"
    COMPARISON = "comparison"
    DATABASE = "database"
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"
    CUSTOM = "custom"


class Instruction(BaseModel):
    raw_text: str
    folder_path: str | None = None
    intent: InstructionIntent = InstructionIntent.CUSTOM
    actions: list[dict[str, Any]] = Field(default_factory=list)
    output_type: OutputType = OutputType.SUMMARY
    filters: dict[str, Any] = Field(default_factory=dict)
    special_instructions: str = ""
    context: list[dict[str, Any]] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)


class ExecutionStep(BaseModel):
    step_number: int
    description: str
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    result: str | None = None
    error: str | None = None
    duration_seconds: float | None = None


class InstructionResult(BaseModel):
    instruction: Instruction
    steps: list[ExecutionStep] = Field(default_factory=list)
    output_content: str = ""
    output_files: list[str] = Field(default_factory=list)
    summary: str = ""
    follow_up_suggestions: list[str] = Field(default_factory=list)
    total_duration_seconds: float | None = None
