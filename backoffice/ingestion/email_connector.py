"""Email ingestion connector (supports raw .eml content or dict)."""
from __future__ import annotations
import email
from typing import Any, Dict, List, Optional
from .base import BaseConnector, RawRecord


class EmailConnector(BaseConnector):
    """Ingests email messages (raw .eml bytes or dict representation)."""

    @property
    def source_type(self) -> str:
        return "email"

    def ingest(self, source: Any) -> List[RawRecord]:
        """
        source: bytes (.eml raw content) or dict with keys:
            subject, sender, recipients, body, date, attachments
        """
        if isinstance(source, bytes):
            return self._ingest_eml(source)
        if isinstance(source, dict):
            return self._ingest_dict(source)
        raise ValueError(f"EmailConnector: unsupported source type {type(source)}")

    def _ingest_eml(self, raw: bytes) -> List[RawRecord]:
        msg = email.message_from_bytes(raw)
        body = ""
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    body += payload.decode(errors="replace")
        data: Dict[str, Any] = {
            "subject": msg.get("subject", ""),
            "sender": msg.get("from", ""),
            "recipients": msg.get("to", ""),
            "date": msg.get("date", ""),
            "body": body,
        }
        return self._ingest_dict(data, raw)

    def _ingest_dict(self, data: Dict[str, Any], raw: Optional[bytes] = None) -> List[RawRecord]:
        text = f"{data.get('subject', '')} {data.get('body', '')}"
        checksum = RawRecord.compute_checksum(raw) if raw else RawRecord.compute_checksum(text.encode())
        return [RawRecord(
            source_type=self.source_type,
            checksum=checksum,
            document_class=self._detect_document_class(text),
            raw_text=text,
            structured_data=data,
            metadata={"sender": data.get("sender", ""), "subject": data.get("subject", "")},
        )]
