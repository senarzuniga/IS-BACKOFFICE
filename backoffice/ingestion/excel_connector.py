"""Excel (.xlsx/.csv) ingestion connector."""
from __future__ import annotations
import io
from typing import Any, List, Dict
from .base import BaseConnector, RawRecord


class ExcelConnector(BaseConnector):
    @property
    def source_type(self) -> str:
        return "excel"

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
            raise ValueError(f"ExcelConnector: unsupported source type {type(source)}")

        records = self._extract_sheets(raw_bytes, file_path)
        return records

    def _extract_sheets(self, raw_bytes: bytes, file_path: str | None) -> List[RawRecord]:
        import pandas as pd
        checksum = RawRecord.compute_checksum(raw_bytes)
        filename = file_path.split("/")[-1] if file_path else None
        records: List[RawRecord] = []
        try:
            xls = pd.ExcelFile(io.BytesIO(raw_bytes))
            for sheet_name in xls.sheet_names:
                df = xls.parse(sheet_name)
                text = df.to_string(index=False)
                data: Dict[str, Any] = {
                    "sheet": sheet_name,
                    "columns": list(df.columns),
                    "rows": df.to_dict(orient="records"),
                    "shape": df.shape,
                }
                records.append(RawRecord(
                    source_type=self.source_type,
                    file_path=file_path,
                    filename=filename,
                    checksum=checksum,
                    document_class=self._detect_document_class(text),
                    raw_text=text[:2000],
                    structured_data=data,
                    metadata={"sheet_name": sheet_name, "rows": df.shape[0], "cols": df.shape[1]},
                ))
        except Exception:
            records.append(RawRecord(
                source_type=self.source_type,
                file_path=file_path,
                filename=filename,
                checksum=checksum,
                raw_text="",
                metadata={"error": "parse_failed"},
            ))
        return records
