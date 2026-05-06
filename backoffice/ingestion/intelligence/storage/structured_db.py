"""Structured data and intelligence output persistence backed by Supabase."""
from __future__ import annotations

import logging
from typing import Any

from backoffice.ingestion.intelligence.models.extracted_data import NormalizedData
from backoffice.ingestion.intelligence.models.intelligence_output import IntelligenceOutput

logger = logging.getLogger(__name__)


class StructuredDB:
    def __init__(self, supabase_client: Any | None) -> None:
        self.supabase = supabase_client

    async def save_normalized_data(self, normalized: NormalizedData) -> None:
        if not self.supabase:
            return
        payload = {
            "source_id": normalized.source_id,
            "source_name": normalized.source_name,
            "url": normalized.url,
            "data_type": normalized.data_type,
            "normalized_content": normalized.normalized_content,
            "confidence_score": normalized.confidence_score,
            "dedupe_key": normalized.dedupe_key,
            "normalized_at": normalized.normalized_at.isoformat(),
        }
        try:
            self.supabase.table("ingestion_structured_data").upsert(
                payload, on_conflict="dedupe_key"
            ).execute()
        except Exception as exc:  # noqa: BLE001
            logger.warning("StructuredDB.save_normalized_data failed: %s", exc)

    async def save_intelligence_outputs(self, outputs: list[IntelligenceOutput]) -> None:
        if not self.supabase or not outputs:
            return
        rows = [
            {
                "type": o.output_type,
                "title": o.title,
                "description": o.description,
                "impact": o.impact,
                "suggested_action": o.suggested_action,
                "source_url": o.source_url,
                "source_id": o.source_id,
                "payload": o.payload,
                "created_at": o.created_at.isoformat(),
            }
            for o in outputs
        ]
        try:
            self.supabase.table("intelligence_outputs").insert(rows).execute()
        except Exception as exc:  # noqa: BLE001
            logger.warning("StructuredDB.save_intelligence_outputs failed: %s", exc)
