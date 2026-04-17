from __future__ import annotations

from pathlib import Path
from .models import RawRecord


class DataIngestionLayer:
    SUPPORTED = {
        "outlook_email",
        "pdf",
        "word",
        "excel",
        "txt",
        "folder_scan",
        "crm",
    }

    def ingest_record(self, source_type: str, content: str, source_id: str, **metadata: str) -> RawRecord:
        if source_type not in self.SUPPORTED:
            raise ValueError(f"Unsupported source type: {source_type}")
        return RawRecord(
            source_type=source_type,
            content=content.strip(),
            source_id=source_id,
            client_reference=metadata.get("client_reference"),
            classification=metadata.get("classification"),
            metadata=metadata,
        )

    def scan_folder(self, folder: str) -> list[RawRecord]:
        records: list[RawRecord] = []
        for path in sorted(Path(folder).glob("**/*")):
            if not path.is_file():
                continue
            ext = path.suffix.lower()
            source_type = {
                ".pdf": "pdf",
                ".docx": "word",
                ".xlsx": "excel",
                ".txt": "txt",
            }.get(ext)
            if source_type is None:
                continue
            records.append(self.ingest_record(source_type, path.read_text(encoding="utf-8", errors="ignore"), str(path)))
        return records
