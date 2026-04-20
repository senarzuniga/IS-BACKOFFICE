"""Folder scanner — dispatches to correct connector by file extension."""
from __future__ import annotations
import os
from typing import List
from .base import RawRecord
from .pdf_connector import PDFConnector
from .word_connector import WordConnector
from .excel_connector import ExcelConnector
from .txt_connector import TxtConnector


_EXT_MAP = {
    ".pdf": PDFConnector(),
    ".docx": WordConnector(),
    ".doc": WordConnector(),
    ".xlsx": ExcelConnector(),
    ".xls": ExcelConnector(),
    ".txt": TxtConnector(),
    ".csv": ExcelConnector(),
}


class FolderScanner:
    """Recursively scans a folder and ingests all supported files."""

    def scan(self, folder_path: str, recursive: bool = True) -> List[RawRecord]:
        records: List[RawRecord] = []
        walker = os.walk(folder_path) if recursive else [(folder_path, [], os.listdir(folder_path))]
        for root, _, files in walker:
            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                connector = _EXT_MAP.get(ext)
                if connector is None:
                    continue
                full_path = os.path.join(root, filename)
                try:
                    records.extend(connector.ingest(full_path))
                except Exception as exc:
                    records.append(RawRecord(
                        source_type=ext.lstrip(".") or "unknown",
                        file_path=full_path,
                        filename=filename,
                        metadata={"error": str(exc)},
                    ))
        return records
