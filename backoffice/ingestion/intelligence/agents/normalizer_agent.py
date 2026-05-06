"""
Normalizer Agent – Layer 3b: Structuring (data unification).

Applies currency conversion, unit normalisation, and deterministic
deduplication keys to raw extraction payloads.
"""
from __future__ import annotations

import logging
from datetime import datetime

from backoffice.ingestion.intelligence.models.extracted_data import ExtractedData, NormalizedData
from backoffice.ingestion.intelligence.normalizers.currency_normalizer import CurrencyNormalizer
from backoffice.ingestion.intelligence.normalizers.product_matcher import ProductMatcher
from backoffice.ingestion.intelligence.normalizers.unit_normalizer import UnitNormalizer

logger = logging.getLogger(__name__)


class NormalizerAgent:
    def __init__(self) -> None:
        self.currency_normalizer = CurrencyNormalizer()
        self.unit_normalizer = UnitNormalizer()
        self.matcher = ProductMatcher()

    async def normalize(self, extracted: ExtractedData) -> NormalizedData:
        payload = dict(extracted.content)

        # --- Currency ---
        price = payload.get("price_estimated")
        if isinstance(price, dict):
            eur_value, eur_ccy = self.currency_normalizer.normalize(
                price.get("value"), price.get("currency")
            )
            payload["price_estimated"] = {"value": eur_value, "currency": eur_ccy}

        # --- Units ---
        specs = payload.get("specifications")
        if isinstance(specs, dict):
            if isinstance(specs.get("speed"), dict):
                sv, su = self.unit_normalizer.normalize_speed(
                    specs["speed"].get("value"), specs["speed"].get("unit")
                )
                specs["speed"] = {"value": sv, "unit": su}
            if isinstance(specs.get("width"), dict):
                wv, wu = self.unit_normalizer.normalize_width(
                    specs["width"].get("value"), specs["width"].get("unit")
                )
                specs["width"] = {"value": wv, "unit": wu}
            payload["specifications"] = specs

        # --- Deduplication key ---
        dedupe_key = self.matcher.dedupe_key(
            payload.get("product_name"),
            payload.get("manufacturer"),
            extracted.url,
        )

        return NormalizedData(
            source_id=extracted.source_id,
            source_name=extracted.source_name,
            url=extracted.url,
            data_type=extracted.data_type,
            normalized_at=datetime.utcnow(),
            normalized_content=payload,
            confidence_score=extracted.confidence_score,
            dedupe_key=dedupe_key,
        )
