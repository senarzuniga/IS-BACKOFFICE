"""Scrapers sub-package."""
from backoffice.ingestion.intelligence.scrapers.static_scraper import StaticScraper
from backoffice.ingestion.intelligence.scrapers.dynamic_scraper import DynamicScraper
from backoffice.ingestion.intelligence.scrapers.antibot_scraper import AntiBotScraper

__all__ = ["StaticScraper", "DynamicScraper", "AntiBotScraper"]
