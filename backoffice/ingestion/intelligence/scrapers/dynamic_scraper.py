"""Dynamic scraper – uses Playwright for JavaScript-heavy pages.

Playwright is optional; falls back gracefully if not installed.
Install with: pip install playwright && playwright install chromium
"""
from __future__ import annotations

import time

try:
    from playwright.async_api import async_playwright
    _PLAYWRIGHT_OK = True
except Exception:  # noqa: BLE001
    async_playwright = None  # type: ignore[assignment]
    _PLAYWRIGHT_OK = False


class DynamicScraper:
    async def scrape(
        self, url: str, wait_for_selector: str | None = None
    ) -> tuple[bool, str | None, int | None, float, str | None]:
        start = time.perf_counter()
        if not _PLAYWRIGHT_OK:
            return False, None, None, 0.0, "playwright not installed – run: pip install playwright && playwright install chromium"

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                response = await page.goto(url, wait_until="networkidle")
                if wait_for_selector:
                    await page.wait_for_selector(wait_for_selector, timeout=10_000)
                html = await page.content()
                status_code = response.status if response else None
                await browser.close()
            return True, html, status_code, (time.perf_counter() - start) * 1000, None
        except Exception as exc:  # noqa: BLE001
            return False, None, None, (time.perf_counter() - start) * 1000, str(exc)
