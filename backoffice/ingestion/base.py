"""Abstract base connector and RawRecord."""
from __future__ import annotations
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from backoffice.models.base import _uuid, _now


class RawRecord(BaseModel):
    """Represents one unit of raw ingested data before cleaning."""
    record_id: str = Field(default_factory=_uuid)
    source_type: str
    file_path: Optional[str] = None
    filename: Optional[str] = None
    checksum: Optional[str] = None
    ingested_at: datetime = Field(default_factory=_now)
    client_ref: Optional[str] = None
    document_class: Optional[str] = None
    raw_text: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "allow"}

    @classmethod
    def compute_checksum(cls, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()


class BaseConnector(ABC):
    """Abstract base class for all ingestion connectors."""

    @property
    @abstractmethod
    def source_type(self) -> str:
        ...

    @abstractmethod
    def ingest(self, source: Any) -> List[RawRecord]:
        """Ingest from source and return list of RawRecords."""
        ...

    def _detect_document_class(self, text: str) -> str:
        text_lower = text.lower()
        if any(k in text_lower for k in ["offre", "offer", "devis", "quotation", "proposal"]):
            return "offer"
        if any(k in text_lower for k in ["contrat", "contract", "agreement"]):
            return "contract"
        if any(k in text_lower for k in ["rapport", "report", "analyse", "analysis"]):
            return "report"
        if any(k in text_lower for k in ["facture", "invoice", "bill"]):
            return "invoice"
        return "other"
