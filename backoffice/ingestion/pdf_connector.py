"""PDF ingestion connector."""
from __future__ import annotations
from typing import Any, List
from .base import BaseConnector, RawRecord


class PDFConnector(BaseConnector):
    @property
    def source_type(self) -> str:
        return "pdf"

    def ingest(self, source: Any) -> List[RawRecord]:
        """source: file path (str) or raw bytes."""
        if isinstance(source, (str, bytes)):
            return self._ingest_pdf(source)
        raise ValueError(f"PDFConnector: unsupported source type {type(source)}")

    def _ingest_pdf(self, source: Any) -> List[RawRecord]:
        raw_bytes: bytes
        file_path: str | None = None
        if isinstance(source, str):
            file_path = source
            with open(source, "rb") as f:
                raw_bytes = f.read()
        else:
            raw_bytes = source

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
            metadata={"page_count": self._count_pages(raw_bytes)},
        )]

    def _extract_text(self, raw_bytes: bytes) -> str:
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=raw_bytes, filetype="pdf")
            return "\n".join(page.get_text() for page in doc)
        except Exception:
            return ""

    def _count_pages(self, raw_bytes: bytes) -> int:
        try:
            import fitz
            doc = fitz.open(stream=raw_bytes, filetype="pdf")
            return len(doc)
        except Exception:
            return 0
