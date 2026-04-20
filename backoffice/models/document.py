"""Document canonical model."""
from __future__ import annotations
from typing import Optional, List
from pydantic import Field
from .base import BaseEntity


class Document(BaseEntity):
    source_type: str  # email | pdf | word | excel | txt
    file_path: Optional[str] = None
    filename: Optional[str] = None
    document_class: str = "other"  # offer | contract | report | invoice | other
    raw_text: Optional[str] = None
    word_count: int = 0
    client_ref: Optional[str] = None
    language: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
