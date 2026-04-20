"""Word (.docx) ingestion connector."""
from __future__ import annotations
from typing import Any, List
from .base import BaseConnector, RawRecord


class WordConnector(BaseConnector):
    @property
    def source_type(self) -> str:
        return "word"

    def ingest(self, source: Any) -> List[RawRecord]:
        """source: file path (str) or raw bytes."""
        if isinstance(source, str):
            with open(source, "rb") as f:
                raw_bytes = f.read()
            file_path = source
        elif isinstance(source, bytes):
            raw_bytes = source
            file_path = None
        else:
            raise ValueError(f"WordConnector: unsupported source type {type(source)}")

        text = self._extract_text(raw_bytes)
        checksum = RawRecord.compute_checksum(raw_bytes)
        filename = file_path.split("/")[-1] if file_path else None
        return [RawRecord(
            source_type=self.source_type,
            file_path=file_path,
            filename=filename,
            checksum=checksum,
            document_class=self._detect_document_class(text),
            raw_text=text,
            metadata={},
        )]

    def _extract_text(self, raw_bytes: bytes) -> str:
        try:
            import io
            from docx import Document
            doc = Document(io.BytesIO(raw_bytes))
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception:
            return ""
