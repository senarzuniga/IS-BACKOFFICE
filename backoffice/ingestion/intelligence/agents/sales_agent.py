"""
Sales Agent – Layer 4: Sales Enablement.

Materialises high/medium-impact intelligence outputs as actionable
records in the Supabase `actions` table (shared with adaptive-sales-engine).
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from backoffice.ingestion.intelligence.models.intelligence_output import IntelligenceOutput

logger = logging.getLogger(__name__)


class SalesAgent:
    def __init__(self, supabase_client: Any | None) -> None:
        self.supabase = supabase_client

    async def create_actions(self, outputs: list[IntelligenceOutput]) -> int:
        """Insert high/medium-impact outputs as commercial actions.

        Returns the number of actions successfully created.
        Writes to the `actions` table so adaptive-sales-engine can consume them.
        """
        if not self.supabase:
            return 0

        created = 0
        for output in outputs:
            if output.impact not in {"high", "medium"}:
                continue
            payload = {
                "name": output.title,
                "goal": output.description,
                "description": output.suggested_action,
                "department": "Commercial",
                "status": "open",
                "importance_score": 90 if output.impact == "high" else 75,
                "strategy_alignment": 85,
                "estimated_hours": 2.0,
                "supportive_content": {
                    "source_url": output.source_url,
                    "intel_type": output.output_type,
                },
                "created_at": datetime.utcnow().isoformat(),
                "last_modified": datetime.utcnow().isoformat(),
            }
            try:
                self.supabase.table("actions").insert(payload).execute()
                created += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning("SalesAgent: could not insert action – %s", exc)
        return created
