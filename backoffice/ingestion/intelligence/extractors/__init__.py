"""Extractors sub-package."""
from backoffice.ingestion.intelligence.extractors.product_extractor import ProductExtractor
from backoffice.ingestion.intelligence.extractors.price_extractor import PriceExtractor
from backoffice.ingestion.intelligence.extractors.spec_extractor import SpecExtractor
from backoffice.ingestion.intelligence.extractors.news_extractor import NewsExtractor

__all__ = ["ProductExtractor", "PriceExtractor", "SpecExtractor", "NewsExtractor"]
