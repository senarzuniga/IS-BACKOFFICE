"""Web Intelligence subsystem — deep crawling, market intel, leads, content aggregation."""
from .crawler import IntelligenceCrawler
from .extractors import MarketExtractor, LeadExtractor, ContentExtractor
from .storage import IntelligenceDB, intelligence_db
from .pipeline import IntelligencePipeline, pipeline, TASK_TYPES

__all__ = [
    "IntelligenceCrawler",
    "MarketExtractor",
    "LeadExtractor",
    "ContentExtractor",
    "IntelligenceDB",
    "intelligence_db",
    "IntelligencePipeline",
    "pipeline",
    "TASK_TYPES",
]
