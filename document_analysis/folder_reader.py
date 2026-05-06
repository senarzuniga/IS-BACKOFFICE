"""FolderReader — discovers and inventories files in a local folder."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Iterator

from document_analysis.models import DocumentType, FolderStats

SUPPORTED_EXTENSIONS: dict[str, DocumentType] = {
    # Documents
    ".pdf": DocumentType.PDF,
    ".docx": DocumentType.DOCX,
    ".doc": DocumentType.DOCX,
    ".docm": DocumentType.DOCX,
    ".rtf": DocumentType.DOCX,
    ".odt": DocumentType.DOCX,
    ".wpd": DocumentType.DOCX,
    ".wps": DocumentType.DOCX,
    ".pages": DocumentType.DOCX,
    # Spreadsheets
    ".xlsx": DocumentType.XLSX,
    ".xls": DocumentType.XLSX,
    ".xlsm": DocumentType.XLSX,
    ".xlsb": DocumentType.XLSX,
    ".ods": DocumentType.XLSX,
    ".numbers": DocumentType.XLSX,
    ".csv": DocumentType.CSV,
    ".tsv": DocumentType.CSV,
    ".tab": DocumentType.CSV,
    # Presentations
    ".pptx": DocumentType.PPTX,
    ".ppt": DocumentType.PPTX,
    ".pptm": DocumentType.PPTX,
    ".odp": DocumentType.PPTX,
    ".key": DocumentType.PPTX,
    # Text
    ".txt": DocumentType.TXT,
    ".md": DocumentType.TXT,
    ".rst": DocumentType.TXT,
    ".log": DocumentType.TXT,
    ".text": DocumentType.TXT,
    ".eml": DocumentType.TXT,
    ".msg": DocumentType.TXT,
    ".emlx": DocumentType.TXT,
    # Structured data
    ".json": DocumentType.JSON,
    ".yaml": DocumentType.JSON,
    ".yml": DocumentType.JSON,
    ".xml": DocumentType.XML,
    # Web
    ".html": DocumentType.HTML,
    ".htm": DocumentType.HTML,
    ".mht": DocumentType.HTML,
    ".mhtml": DocumentType.HTML,
    # Images and archives are discoverable but parsed as unknown unless OCR/extractors are available.
    ".png": DocumentType.UNKNOWN,
    ".jpg": DocumentType.UNKNOWN,
    ".jpeg": DocumentType.UNKNOWN,
    ".tiff": DocumentType.UNKNOWN,
    ".tif": DocumentType.UNKNOWN,
    ".bmp": DocumentType.UNKNOWN,
    ".gif": DocumentType.UNKNOWN,
    ".webp": DocumentType.UNKNOWN,
    ".heic": DocumentType.UNKNOWN,
    ".zip": DocumentType.UNKNOWN,
    ".rar": DocumentType.UNKNOWN,
    ".7z": DocumentType.UNKNOWN,
}


class FolderReader:
    """Discovers and inventories files in a local directory tree."""

    def __init__(self, recursive: bool = True, max_file_size_mb: float = 50.0) -> None:
        self.recursive = recursive
        self.max_file_size_bytes = int(max_file_size_mb * 1024 * 1024)

    def discover_files(
        self,
        folder_path: str | Path,
        extensions: list[str] | None = None,
        recursive: bool = True,
        file_types: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        min_size_bytes: int = 0,
        max_size_bytes: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[dict]:
        """Return a list of file info dicts for all supported files under *folder_path*.

        Each dict has keys: path, name, extension, doc_type, size_bytes, modified_at.
        Files exceeding *max_file_size_bytes* are included but flagged.
        """
        folder = Path(folder_path).expanduser().resolve()
        if not folder.exists():
            raise FileNotFoundError(f"Folder not found: {folder}")
        if not folder.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {folder}")

        allowed_exts = {e.lower() for e in (extensions or [])}
        normalized_file_types = {ft.lower().lstrip(".") for ft in (file_types or [])}
        exclude = set(exclude_patterns or [])
        # Keep exclusions conservative to avoid hiding real business documents.
        exclude.update(["Thumbs.db", ".DS_Store", "desktop.ini"])

        results: list[dict] = []
        for file_path in self._iter_files(folder, recursive=recursive):
            if file_path.name in exclude:
                continue

            ext = file_path.suffix.lower()

            if normalized_file_types and ext.lstrip(".") not in normalized_file_types:
                continue

            if allowed_exts and ext not in allowed_exts:
                continue

            try:
                stat = file_path.stat()
            except OSError:
                continue

            if min_size_bytes > 0 and stat.st_size < min_size_bytes:
                continue
            if max_size_bytes is not None and stat.st_size > max_size_bytes:
                continue

            modified_at = datetime.fromtimestamp(stat.st_mtime)
            if date_from and modified_at < date_from:
                continue
            if date_to and modified_at > date_to:
                continue

            results.append(
                {
                    "path": str(file_path),
                    "name": file_path.name,
                    "extension": ext,
                    "doc_type": SUPPORTED_EXTENSIONS.get(ext, DocumentType.UNKNOWN).value,
                    "size_bytes": stat.st_size,
                    "modified_at": modified_at.isoformat(),
                    "oversized": stat.st_size > self.max_file_size_bytes,
                }
            )

        results.sort(key=lambda x: x["name"].lower())
        return results

    def get_folder_stats(self, folder_path: str | Path) -> FolderStats:
        """Return aggregate statistics for a folder without loading file contents."""
        folder = Path(folder_path).expanduser().resolve()
        all_files: list[dict] = []

        for file_path in self._iter_files(folder):
            ext = file_path.suffix.lower()
            try:
                stat = file_path.stat()
            except OSError:
                continue

            all_files.append(
                {
                    "extension": ext,
                    "doc_type": SUPPORTED_EXTENSIONS.get(ext, DocumentType.UNKNOWN).value,
                    "size_bytes": stat.st_size,
                }
            )

        files_by_type: dict[str, int] = {}
        total_size = 0
        for f in all_files:
            dt = f["doc_type"]
            files_by_type[dt] = files_by_type.get(dt, 0) + 1
            total_size += f["size_bytes"]

        return FolderStats(
            folder_path=str(folder),
            total_files=len(all_files),
            supported_files=sum(
                1 for f in all_files if f["doc_type"] != DocumentType.UNKNOWN.value
            ),
            unsupported_files=sum(
                1 for f in all_files if f["doc_type"] == DocumentType.UNKNOWN.value
            ),
            total_size_bytes=total_size,
            files_by_type=files_by_type,
        )

    def _iter_files(self, folder: Path, recursive: bool | None = None) -> Iterator[Path]:
        use_recursive = self.recursive if recursive is None else recursive
        if use_recursive:
            for root, _dirs, files in os.walk(folder):
                for name in files:
                    yield Path(root) / name
        else:
            for item in folder.iterdir():
                if item.is_file():
                    yield item
