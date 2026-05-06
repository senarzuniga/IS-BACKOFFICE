"""
Extractor Agent – Layer 3a: Structuring (semantic extraction).

Converts raw HTML into typed, structured JSON payloads using LLMs or
regex fallbacks when no API key is available.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from typing import Any

from backoffice.ingestion.intelligence.extractors.news_extractor import NewsExtractor
from backoffice.ingestion.intelligence.extractors.price_extractor import PriceExtractor
from backoffice.ingestion.intelligence.extractors.product_extractor import ProductExtractor
from backoffice.ingestion.intelligence.extractors.spec_extractor import SpecExtractor
from backoffice.ingestion.intelligence.models.extracted_data import ExtractedData

logger = logging.getLogger(__name__)


class ExtractorAgent:
    def __init__(self, openai_client: Any | None) -> None:
        self.product_extractor = ProductExtractor(openai_client)
        self.price_extractor = PriceExtractor()
        self.spec_extractor = SpecExtractor()
        self.news_extractor = NewsExtractor()

    async def extract(
        self,
        html: str,
        source_id: str,
        source_name: str,
        url: str,
        data_type: str,
    ) -> ExtractedData:
        if data_type == "news":
            payload, confidence = await self.news_extractor.extract(html)
        elif data_type == "price":
            payload, confidence = await self.price_extractor.extract(html)
        elif data_type == "specs":
            payload, confidence = await self.spec_extractor.extract(html)
        else:
            payload, confidence = await self.product_extractor.extract(html, source_name, url)

        content_hash = hashlib.sha256(html.encode("utf-8", errors="ignore")).hexdigest()
        logger.debug("Extracted %s data from %s (confidence=%.2f)", data_type, url, confidence)
        return ExtractedData(
            source_id=source_id,
            source_name=source_name,
            url=url,
            data_type=data_type,
            extracted_at=datetime.utcnow(),
            content=payload,
            confidence_score=confidence,
            content_hash=content_hash,
        )
