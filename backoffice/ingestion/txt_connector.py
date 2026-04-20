"""Plain text ingestion connector."""
from __future__ import annotations
from typing import Any, List
from .base import BaseConnector, RawRecord


class TxtConnector(BaseConnector):
    @property
    def source_type(self) -> str:
        return "txt"

    def ingest(self, source: Any) -> List[RawRecord]:
        """source: file path (str) or raw bytes or str content."""
        if isinstance(source, str) and len(source) < 1024 and source.endswith(".txt"):
            with open(source, "rb") as f:
                raw_bytes = f.read()
            file_path = source
        elif isinstance(source, str):
            raw_bytes = source.encode()
            file_path = None
        elif isinstance(source, bytes):
            raw_bytes = source
            file_path = None
        else:
            raise ValueError(f"TxtConnector: unsupported source type {type(source)}")

        text = raw_bytes.decode(errors="replace")
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
