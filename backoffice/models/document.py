"""Document canonical model."""
from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import Field
from .base import BaseEntity


class Document(BaseEntity):
    source_type: str  # email | pdf | word | excel | txt | pptx | html | markdown
    file_path: Optional[str] = None
    filename: Optional[str] = None
    document_class: str = "other"  # offer | contract | report | invoice | whitepaper | proposal | landing_page | other
    raw_text: Optional[str] = None
    word_count: int = 0
    client_ref: Optional[str] = None
    language: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    document_tree: Dict[str, Any] = Field(default_factory=dict)
    style_tokens: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    knowledge_links: List[Dict[str, Any]] = Field(default_factory=list)
    mission_links: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    version_history: List[Dict[str, Any]] = Field(default_factory=list)
    publication_targets: List[str] = Field(default_factory=list)
    current_version: Optional[str] = None
