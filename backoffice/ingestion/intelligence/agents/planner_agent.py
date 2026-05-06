"""
Planner Agent – Layer 1: Discovery.

Decides WHAT to scrape, WHEN to scrape it, and at what priority.
Uses a min-heap (priority queue) so HIGH-priority jobs are always processed first.
"""
from __future__ import annotations

import asyncio
import heapq
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from backoffice.ingestion.intelligence.models.source_config import (
    PRIORITY_WEIGHT,
    ScrapingJob,
    ScrapingPriority,
    SourceConfig,
)
from backoffice.ingestion.intelligence.sources.source_registry import SourceRegistry

logger = logging.getLogger(__name__)


class PlannerAgent:
    """
    Orchestrates scraping planning:
    - Loads sources from config/sources.yaml
    - Identifies due sources (by schedule)
    - Handles event-triggered sources
    - Maintains a priority-heap job queue
    """

    def __init__(
        self,
        supabase_client: Any | None,
        config_path: str | Path = "config/sources.yaml",
    ) -> None:
        self.supabase = supabase_client
        self.registry = SourceRegistry(Path(config_path))
        self.sources: list[SourceConfig] = self._safe_load()
        self._priority_heap: list[tuple[int, float, ScrapingJob]] = []
        self._lock = asyncio.Lock()

    def _safe_load(self) -> list[SourceConfig]:
        try:
            return self.registry.load()
        except Exception as exc:  # noqa: BLE001
            logger.warning("PlannerAgent: could not load sources.yaml – %s", exc)
            return []

    # ------------------------------------------------------------------
    # Due / triggered detection
    # ------------------------------------------------------------------

    def _is_due(self, source: SourceConfig, now: datetime) -> bool:
        if not source.is_active:
            return False
        if source.last_scraped is None:
            return True
        elapsed_hours = (now - source.last_scraped).total_seconds() / 3600
        return elapsed_hours >= source.scraping_frequency_hours

    def get_due_sources(self) -> list[SourceConfig]:
        now = datetime.now()
        return [s for s in self.sources if self._is_due(s, now)]

    def get_triggered_sources(self, events: list[dict]) -> list[SourceConfig]:
        if not events:
            return []
        by_id = {s.id: s for s in self.sources}
        triggered: dict[str, SourceConfig] = {}
        for event in events:
            source_id = event.get("source_id")
            event_type = event.get("type")
            if source_id and source_id in by_id:
                source = by_id[source_id]
                if event_type in source.event_triggers:
                    triggered[source.id] = source
            else:
                for source in self.sources:
                    if event_type in source.event_triggers:
                        triggered[source.id] = source
        return list(triggered.values())

    # ------------------------------------------------------------------
    # Job creation & queue management
    # ------------------------------------------------------------------

    async def create_scraping_jobs(
        self, sources: list[SourceConfig], triggered_by: str
    ) -> list[ScrapingJob]:
        now = datetime.now()
        return [
            ScrapingJob(
                source_id=s.id,
                source_name=s.name,
                url=s.url,
                scraper_type=s.scraper_type,
                priority=s.priority,
                triggered_by=triggered_by,
                scheduled_at=now,
                selectors=s.selectors,
                data_type=s.data_type,
            )
            for s in sources
        ]

    async def _enqueue(self, job: ScrapingJob) -> None:
        async with self._lock:
            weight = PRIORITY_WEIGHT[job.priority]
            heapq.heappush(self._priority_heap, (weight, job.scheduled_at.timestamp(), job))

    @property
    def queue_size(self) -> int:
        return len(self._priority_heap)

    async def get_next_job(self) -> ScrapingJob | None:
        async with self._lock:
            if not self._priority_heap:
                return None
            _, _, job = heapq.heappop(self._priority_heap)
            return job

    # ------------------------------------------------------------------
    # Planning cycle
    # ------------------------------------------------------------------

    async def run_planning_cycle(self, events: list[dict] | None = None) -> None:
        events = events or []
        due_sources = self.get_due_sources()
        triggered_sources = self.get_triggered_sources(events)

        jobs: list[ScrapingJob] = []
        jobs.extend(await self.create_scraping_jobs(due_sources, "schedule"))
        jobs.extend(await self.create_scraping_jobs(triggered_sources, "event"))

        # Deduplicate by source_id + triggered_by
        dedup: dict[str, ScrapingJob] = {f"{j.source_id}:{j.triggered_by}": j for j in jobs}
        for job in dedup.values():
            await self._enqueue(job)

        logger.info(
            "Planner enqueued %d jobs (schedule=%d, event=%d)",
            len(dedup),
            len(due_sources),
            len(triggered_sources),
        )
        await self._log_planning_cycle(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "scheduled_jobs": len(due_sources),
                "event_jobs": len(triggered_sources),
                "queue_size": self.queue_size,
            }
        )

    async def _log_planning_cycle(self, payload: dict) -> None:
        if not self.supabase:
            return
        try:
            self.supabase.table("ingestion_planning_log").insert(payload).execute()
        except Exception as exc:  # noqa: BLE001
            logger.debug("Could not persist planner audit log: %s", exc)
