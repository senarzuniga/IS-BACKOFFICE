"""
Intelligent Ingestion Pipeline
================================
Orchestrates the full 4-layer multi-agent intelligence cycle:

    Layer 1: Discovery  → PlannerAgent schedules + event-driven jobs
    Layer 2: Extraction → ScraperAgent fetches HTML
    Layer 3: Structuring → ExtractorAgent + NormalizerAgent convert to JSON
    Layer 4: Intelligence → IntelligenceAgent + SalesAgent generate insights

The pipeline gracefully degrades when external dependencies are absent:
- No Supabase client → storage operations are no-ops
- No OpenAI client  → LLM extraction falls back to regex
- No Playwright     → dynamic scraping reports a clear error
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from backoffice.ingestion.intelligence.agents.extractor_agent import ExtractorAgent
from backoffice.ingestion.intelligence.agents.intelligence_agent import IntelligenceAgent
from backoffice.ingestion.intelligence.agents.normalizer_agent import NormalizerAgent
from backoffice.ingestion.intelligence.agents.planner_agent import PlannerAgent
from backoffice.ingestion.intelligence.agents.sales_agent import SalesAgent
from backoffice.ingestion.intelligence.agents.scraper_agent import ScraperAgent
from backoffice.ingestion.intelligence.storage.raw_storage import RawStorage
from backoffice.ingestion.intelligence.storage.structured_db import StructuredDB

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Full intelligent ingestion pipeline."""

    def __init__(
        self,
        supabase_client: Any | None,
        openai_client: Any | None,
        config_path: str = "config/sources.yaml",
    ) -> None:
        self.planner = PlannerAgent(supabase_client, config_path=config_path)
        self.scraper = ScraperAgent()
        self.extractor = ExtractorAgent(openai_client)
        self.normalizer = NormalizerAgent()
        self.intelligence = IntelligenceAgent(openai_client)
        self.sales = SalesAgent(supabase_client)
        self.raw_storage = RawStorage(supabase_client)
        self.structured_db = StructuredDB(supabase_client)

        self.stats: dict[str, int] = {
            "jobs_processed": 0,
            "successful_scrapes": 0,
            "failed_scrapes": 0,
            "extractions_done": 0,
            "actions_created": 0,
        }

    # ------------------------------------------------------------------
    # Single job processing
    # ------------------------------------------------------------------

    async def process_job(self, job) -> None:
        logger.info("Processing job: %s – %s", job.source_name, job.url)

        # Layer 2 – Scrape
        result = await self.scraper.scrape(
            url=job.url,
            source_id=job.source_id,
            source_name=job.source_name,
            scraper_type=job.scraper_type,
            wait_for_selector=job.selectors.get("wait_for") if job.selectors else None,
        )

        if not result.success or not result.html_content:
            await self.raw_storage.save_error(
                job.source_id,
                job.source_name,
                job.url,
                result.error_message or "unknown error",
            )
            self.stats["failed_scrapes"] += 1
            logger.warning("Scrape failed for %s: %s", job.source_name, result.error_message)
            return

        # Layer 3a – Extract
        extracted = await self.extractor.extract(
            html=result.html_content,
            source_id=job.source_id,
            source_name=job.source_name,
            url=job.url,
            data_type=job.data_type,
        )

        # Persist raw HTML
        await self.raw_storage.save_html(
            job.source_id,
            job.source_name,
            job.url,
            result.html_content,
            extracted.content_hash,
        )

        # Layer 3b – Normalise
        normalized = await self.normalizer.normalize(extracted)
        await self.structured_db.save_normalized_data(normalized)

        # Layer 4 – Intelligence
        intel_outputs = await self.intelligence.analyze_record(
            source_id=normalized.source_id,
            source_name=normalized.source_name,
            source_url=normalized.url,
            payload=normalized.normalized_content,
        )
        await self.structured_db.save_intelligence_outputs(intel_outputs)

        # Layer 4 – Sales enablement (writes to shared `actions` table)
        created = await self.sales.create_actions(intel_outputs)

        self.stats["jobs_processed"] += 1
        self.stats["successful_scrapes"] += 1
        self.stats["extractions_done"] += 1
        self.stats["actions_created"] += created
        logger.info("Job completed: %s (%d intel outputs, %d actions)", job.source_name, len(intel_outputs), created)

    # ------------------------------------------------------------------
    # Cycle runner
    # ------------------------------------------------------------------

    async def run_cycle_once(self, events: list[dict] | None = None) -> dict:
        """Run one full planning + processing cycle and return stats."""
        await self.planner.run_planning_cycle(events=events or [])
        while True:
            job = await self.planner.get_next_job()
            if not job:
                break
            await self.process_job(job)
            await asyncio.sleep(0.2)   # polite delay between requests
        await self.intelligence.run_analysis_cycle()
        return dict(self.stats)

    async def run_continuous_cycle(self, interval_seconds: int = 300) -> None:
        """Run cycles indefinitely with *interval_seconds* pause between cycles."""
        logger.info("Starting continuous intelligent ingestion pipeline")
        while True:
            try:
                stats = await self.run_cycle_once(events=[])
                logger.info("Cycle completed: %s", stats)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Pipeline cycle error: %s", exc)
            await asyncio.sleep(interval_seconds)

    def get_stats(self) -> dict:
        return dict(self.stats)

    def reset_stats(self) -> None:
        for key in self.stats:
            self.stats[key] = 0


# ------------------------------------------------------------------
# Factory helper
# ------------------------------------------------------------------

def build_pipeline(
    supabase_client: Any | None = None,
    openai_client: Any | None = None,
    config_path: str = "config/sources.yaml",
) -> IngestionPipeline:
    """Construct a ready-to-use IngestionPipeline."""
    return IngestionPipeline(
        supabase_client=supabase_client,
        openai_client=openai_client,
        config_path=config_path,
    )


if __name__ == "__main__":
    pipeline = build_pipeline()
    print("Intelligent Ingestion Pipeline ready", datetime.utcnow().isoformat())
    print("Sources loaded:", len(pipeline.planner.sources))
