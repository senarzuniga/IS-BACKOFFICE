"""
backoffice.ingestion.intelligence
4-layer multi-agent intelligent ingestion system.

Layers:
    1. Discovery  – PlannerAgent schedules and prioritises scraping jobs
    2. Extraction – ScraperAgent fetches HTML; ExtractorAgent converts to JSON
    3. Structuring – NormalizerAgent unifies currencies, units, and deduplication keys
    4. Intelligence – IntelligenceAgent & SalesAgent produce actionable outputs

Entry point: backoffice.ingestion.intelligence.pipeline.IngestionPipeline
"""
from __future__ import annotations

__all__ = ["IngestionPipeline", "build_pipeline"]

from backoffice.ingestion.intelligence.pipeline import IngestionPipeline, build_pipeline
