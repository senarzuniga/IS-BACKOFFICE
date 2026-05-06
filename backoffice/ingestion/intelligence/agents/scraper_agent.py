"""
Scraper Agent – Layer 2: Extraction.

Routes scraping jobs to the appropriate scraper implementation:
- static  → StaticScraper  (requests, fast, no JS)
- dynamic → DynamicScraper (Playwright, handles JS-rendered pages)
- antibot → AntiBotScraper (randomised UA + delays)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from backoffice.ingestion.intelligence.scrapers.antibot_scraper import AntiBotScraper
from backoffice.ingestion.intelligence.scrapers.dynamic_scraper import DynamicScraper
from backoffice.ingestion.intelligence.scrapers.static_scraper import StaticScraper

logger = logging.getLogger(__name__)


@dataclass
class ScrapingResult:
    source_id: str
    source_name: str
    url: str
    success: bool
    html_content: str | None = None
    error_message: str | None = None
    response_time_ms: float = 0
    status_code: int | None = None
    scraper_type: str = "static"


class ScraperAgent:
    def __init__(self) -> None:
        self.static_scraper = StaticScraper()
        self.dynamic_scraper = DynamicScraper()
        self.antibot_scraper = AntiBotScraper()

    async def scrape(
        self,
        url: str,
        source_id: str,
        source_name: str,
        scraper_type: str,
        wait_for_selector: str | None = None,
        **_kwargs,
    ) -> ScrapingResult:
        logger.info("Scraping %s via %s scraper", url, scraper_type)
        if scraper_type == "dynamic":
            ok, html, status, elapsed, err = await self.dynamic_scraper.scrape(
                url, wait_for_selector=wait_for_selector
            )
        elif scraper_type == "antibot":
            ok, html, status, elapsed, err = await self.antibot_scraper.scrape(url)
        else:
            ok, html, status, elapsed, err = await self.static_scraper.scrape(url)

        return ScrapingResult(
            source_id=source_id,
            source_name=source_name,
            url=url,
            success=ok,
            html_content=html,
            error_message=err,
            response_time_ms=elapsed,
            status_code=status,
            scraper_type=scraper_type,
        )
