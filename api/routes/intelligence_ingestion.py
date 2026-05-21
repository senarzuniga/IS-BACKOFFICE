"""
FastAPI router – Intelligent Ingestion API
==========================================
Exposes endpoints to trigger, monitor, and query the multi-agent ingestion pipeline.

Prefix: /intelligence-ingestion
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/intelligence-ingestion", tags=["Intelligence Ingestion"])


# ------------------------------------------------------------------
# Lazy pipeline singleton (built on first use to avoid import-time side effects)
# ------------------------------------------------------------------

_pipeline = None


def _get_pipeline():
    global _pipeline  # noqa: PLW0603
    if _pipeline is None:
        from backoffice.ingestion.intelligence.pipeline import build_pipeline

        supabase_client = _try_build_supabase()
        openai_client = _try_build_openai()
        _pipeline = build_pipeline(
            supabase_client=supabase_client,
            openai_client=openai_client,
        )
    return _pipeline


def _try_build_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception:  # noqa: BLE001
        return None


def _try_build_openai():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import AsyncOpenAI
        return AsyncOpenAI(api_key=api_key)
    except Exception:  # noqa: BLE001
        return None


# ------------------------------------------------------------------
# Request / Response models
# ------------------------------------------------------------------

class ManualTriggerRequest(BaseModel):
    url: str = Field(..., description="URL to scrape immediately")
    source_id: str = Field(default="manual", description="Logical source identifier")
    source_name: str = Field(default="Manual Trigger", description="Display name")
    scraper_type: str = Field(default="static", description="static | dynamic | antibot")
    data_type: str = Field(default="product", description="product | news | price | specs")


class EventTriggerRequest(BaseModel):
    events: list[dict] = Field(
        default_factory=list,
        description="List of events like {'type': 'website_change', 'source_id': 'fosber_home'}",
    )


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@router.get("/status")
def get_status():
    """Return pipeline health and current stats."""
    try:
        pipeline = _get_pipeline()
        return {
            "status": "ok",
            "sources_loaded": len(pipeline.planner.sources),
            "queue_size": pipeline.planner.queue_size,
            "stats": pipeline.get_stats(),
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "degraded", "error": str(exc)}


@router.get("/sources")
def list_sources():
    """List all configured intelligence sources."""
    try:
        pipeline = _get_pipeline()
        return [
            {
                "id": s.id,
                "name": s.name,
                "url": s.url,
                "tier": s.tier,
                "priority": s.priority,
                "scraper_type": s.scraper_type,
                "data_type": s.data_type,
                "is_active": s.is_active,
                "scraping_frequency_hours": s.scraping_frequency_hours,
                "last_scraped": s.last_scraped.isoformat() if s.last_scraped else None,
            }
            for s in pipeline.planner.sources
        ]
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/run-cycle")
async def run_cycle(background_tasks: BackgroundTasks):
    """Trigger a full planning + scraping + intelligence cycle (async)."""
    pipeline = _get_pipeline()
    background_tasks.add_task(_run_cycle_task, pipeline)
    return {"message": "Ingestion cycle started in background", "queue_size": pipeline.planner.queue_size}


async def _run_cycle_task(pipeline) -> None:
    try:
        stats = await pipeline.run_cycle_once(events=[])
        logger.info("Background cycle completed: %s", stats)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Background cycle error: %s", exc)


@router.post("/trigger-events")
async def trigger_events(request: EventTriggerRequest, background_tasks: BackgroundTasks):
    """Push custom events to trigger event-driven scraping."""
    pipeline = _get_pipeline()
    background_tasks.add_task(_run_event_cycle, pipeline, request.events)
    return {"message": f"Event-driven cycle queued for {len(request.events)} event(s)"}


async def _run_event_cycle(pipeline, events: list[dict]) -> None:
    try:
        await pipeline.run_cycle_once(events=events)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Event cycle error: %s", exc)


@router.post("/scrape-now")
async def scrape_now(request: ManualTriggerRequest):
    """Scrape a single URL immediately and return extracted intelligence."""
    from backoffice.ingestion.intelligence.agents.scraper_agent import ScraperAgent
    from backoffice.ingestion.intelligence.agents.extractor_agent import ExtractorAgent
    from backoffice.ingestion.intelligence.agents.normalizer_agent import NormalizerAgent
    from backoffice.ingestion.intelligence.agents.intelligence_agent import IntelligenceAgent

    openai_client = _try_build_openai()
    scraper = ScraperAgent()
    extractor = ExtractorAgent(openai_client)
    normalizer = NormalizerAgent()
    intel_agent = IntelligenceAgent(openai_client)

    scrape_result = await scraper.scrape(
        url=request.url,
        source_id=request.source_id,
        source_name=request.source_name,
        scraper_type=request.scraper_type,
    )

    if not scrape_result.success:
        raise HTTPException(status_code=422, detail=f"Scraping failed: {scrape_result.error_message}")

    extracted = await extractor.extract(
        html=scrape_result.html_content,
        source_id=request.source_id,
        source_name=request.source_name,
        url=request.url,
        data_type=request.data_type,
    )
    normalized = await normalizer.normalize(extracted)
    intel_outputs = await intel_agent.analyze_record(
        source_id=normalized.source_id,
        source_name=normalized.source_name,
        source_url=normalized.url,
        payload=normalized.normalized_content,
    )

    return {
        "url": request.url,
        "scraper_type": request.scraper_type,
        "data_type": request.data_type,
        "response_time_ms": scrape_result.response_time_ms,
        "confidence_score": normalized.confidence_score,
        "extracted": normalized.normalized_content,
        "intelligence": [
            {
                "type": o.output_type,
                "title": o.title,
                "description": o.description,
                "impact": o.impact,
                "suggested_action": o.suggested_action,
            }
            for o in intel_outputs
        ],
    }


@router.get("/stats")
def get_stats():
    """Return current pipeline processing statistics."""
    pipeline = _get_pipeline()
    return pipeline.get_stats()


@router.post("/stats/reset")
def reset_stats():
    """Reset pipeline processing counters."""
    pipeline = _get_pipeline()
    pipeline.reset_stats()
    return {"message": "Stats reset"}
