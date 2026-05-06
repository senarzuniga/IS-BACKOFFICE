"""Raw HTML and error storage backed by Supabase (no-op when client is None)."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class RawStorage:
    def __init__(self, supabase_client: Any | None) -> None:
        self.supabase = supabase_client

    async def save_html(
        self,
        source_id: str,
        source_name: str,
        url: str,
        html: str,
        content_hash: str,
    ) -> None:
        if not self.supabase:
            return
        payload = {
            "source_id": source_id,
            "source_name": source_name,
            "url": url,
            "html_content": html[:2_000_000],
            "content_hash": content_hash,
            "captured_at": datetime.utcnow().isoformat(),
        }
        try:
            self.supabase.table("ingestion_raw_html").insert(payload).execute()
        except Exception as exc:  # noqa: BLE001
            logger.warning("RawStorage.save_html failed: %s", exc)

    async def save_error(
        self,
        source_id: str,
        source_name: str,
        url: str,
        error_message: str,
    ) -> None:
        if not self.supabase:
            return
        payload = {
            "source_id": source_id,
            "source_name": source_name,
            "url": url,
            "error_message": error_message,
            "captured_at": datetime.utcnow().isoformat(),
        }
        try:
            self.supabase.table("ingestion_errors").insert(payload).execute()
        except Exception as exc:  # noqa: BLE001
            logger.warning("RawStorage.save_error failed: %s", exc)
