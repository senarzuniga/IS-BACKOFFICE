"""
Intelligence Agent – Layer 4: Intelligence.

Analyses normalised data to produce actionable intelligence outputs:
- Competitor movement signals
- Pricing band alerts
- Market trend signals
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from backoffice.ingestion.intelligence.intel.competitive_intel import build_competitor_signal
from backoffice.ingestion.intelligence.intel.market_intel import build_market_signal
from backoffice.ingestion.intelligence.intel.pricing_intel import build_pricing_insight
from backoffice.ingestion.intelligence.intel.sales_assets import build_sales_asset
from backoffice.ingestion.intelligence.models.intelligence_output import IntelligenceOutput

logger = logging.getLogger(__name__)


class IntelligenceAgent:
    def __init__(self, openai_client: Any | None = None) -> None:
        self.openai = openai_client

    async def analyze_record(
        self,
        source_id: str,
        source_name: str,
        source_url: str,
        payload: dict,
    ) -> list[IntelligenceOutput]:
        outputs: list[IntelligenceOutput] = []

        # 1. Competitor movement
        competitor = build_competitor_signal(source_name, payload)
        battle_card = build_sales_asset(competitor["title"], competitor["message"], source_url)
        outputs.append(
            IntelligenceOutput(
                output_type="competitor_movement",
                title=competitor["title"],
                description=competitor["message"],
                impact="medium",
                suggested_action="Review positioning and update opportunity notes.",
                source_url=source_url,
                source_id=source_id,
                created_at=datetime.utcnow(),
                payload=battle_card,
            )
        )

        # 2. Pricing alert (only when price data present)
        pricing = build_pricing_insight(payload)
        if pricing:
            outputs.append(
                IntelligenceOutput(
                    output_type="pricing_alert",
                    title="Competitive pricing band updated",
                    description=pricing["message"],
                    impact=pricing["impact"],
                    suggested_action="Recalculate target margin and update offer strategy.",
                    source_url=source_url,
                    source_id=source_id,
                    created_at=datetime.utcnow(),
                    payload=pricing,
                )
            )

        # 3. Market trend (news-type records)
        market = build_market_signal(payload)
        if market:
            outputs.append(
                IntelligenceOutput(
                    output_type="market_trend",
                    title="Industry news impact",
                    description=market["message"],
                    impact=market["impact"],
                    suggested_action="Create commercial follow-up action for affected segment.",
                    source_url=source_url,
                    source_id=source_id,
                    created_at=datetime.utcnow(),
                    payload=market,
                )
            )

        logger.debug("IntelligenceAgent produced %d outputs for %s", len(outputs), source_id)
        return outputs

    async def run_analysis_cycle(self) -> None:
        """Hook point for batch-level digest analysis (daily/weekly)."""
        return
