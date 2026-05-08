"""Advanced multi-level web crawler with robots.txt compliance and optional JS rendering."""
from __future__ import annotations

import logging
import re
import time
from collections import deque
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Optional Playwright for JS rendering
try:
    from playwright.sync_api import sync_playwright  # type: ignore
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class IntelligenceCrawler:
    """
    Multi-level BFS web crawler.

    Features:
    - robots.txt compliance (cached per domain)
    - Optional Playwright JS rendering
    - Keyword-based page filtering
    - Rate limiting / polite delay
    - Domain scoping
    """

    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    def __init__(self, delay: float = 0.8, timeout: int = 15):
        self.delay = delay
        self.timeout = timeout
        self.session = self._create_session()
        self._robots_cache: Dict[str, RobotFileParser] = {}

    # ── Session & Headers ─────────────────────────────────────────

    def _create_session(self) -> requests.Session:
        s = requests.Session()
        s.headers.update({
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            # Keep to encodings requests decodes reliably without extra codecs.
            "Accept-Encoding": "gzip, deflate",
        })
        return s

    # ── robots.txt ────────────────────────────────────────────────

    def _get_robots(self, url: str) -> RobotFileParser:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin not in self._robots_cache:
            rp = RobotFileParser()
            try:
                robots_url = f"{origin}/robots.txt"
                resp = self.session.get(robots_url, timeout=self.timeout)
                resp.raise_for_status()

                # Some sites publish robots.txt with malformed CRLF sequences
                # (e.g. double carriage returns) that RobotFileParser.read()
                # can misinterpret. Normalize before parsing.
                normalised = resp.text.replace("\r", "")
                rp.set_url(robots_url)
                rp.parse(normalised.splitlines())
            except Exception:
                # Fallback to stdlib network read if direct parsing fails.
                try:
                    rp.set_url(f"{origin}/robots.txt")
                    rp.read()
                except Exception:
                    pass
            self._robots_cache[origin] = rp
        return self._robots_cache[origin]

    def is_allowed(self, url: str) -> bool:
        try:
            rp = self._get_robots(url)
            return rp.can_fetch(self.USER_AGENT, url)
        except Exception:
            return True

    # ── Page Fetching ─────────────────────────────────────────────

    def fetch_page(self, url: str, use_js: bool = False) -> Optional[str]:
        """Fetch page HTML; uses Playwright when requested and available."""
        if use_js and PLAYWRIGHT_AVAILABLE:
            return self._fetch_with_playwright(url)
        return self._fetch_with_requests(url)

    def _fetch_with_requests(self, url: str) -> Optional[str]:
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            logger.debug(f"[requests] {url}: {e}")
            return None

    def _fetch_with_playwright(self, url: str) -> Optional[str]:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                ctx = browser.new_context(user_agent=self.USER_AGENT)
                page = ctx.new_page()
                page.goto(url, wait_until="networkidle", timeout=self.timeout * 1000)
                html = page.content()
                browser.close()
            return html
        except Exception as e:
            logger.warning(f"[playwright] {url}: {e} — retrying with requests")
            return self._fetch_with_requests(url)

    # ── BFS Crawl ─────────────────────────────────────────────────

    def crawl(
        self,
        start_urls: List[str],
        max_pages: int = 30,
        max_depth: int = 2,
        use_js: bool = False,
        same_domain: bool = True,
        keywords: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> List[Dict[str, Any]]:
        """
        BFS multi-level crawl.

        Args:
            start_urls:       Seed URLs to begin crawling.
            max_pages:        Maximum pages to collect.
            max_depth:        Maximum link depth from seed.
            use_js:           Use Playwright for JS rendering.
            same_domain:      Only follow links within seed domains.
            keywords:         If set, only keep pages matching at least one keyword.
            exclude_patterns: URL fragments to skip (e.g. ['/login', '/cart']).
            progress_callback: Called with each status message.

        Returns:
            List of page dicts: url, title, text, html, links, depth, crawled_at.
        """
        visited: Set[str] = set()
        queue: deque = deque()
        pages: List[Dict[str, Any]] = []

        allowed_domains: Set[str] = {urlparse(u).netloc for u in start_urls}
        exclude_patterns = exclude_patterns or []

        def log(msg: str) -> None:
            logger.info(msg)
            if progress_callback:
                progress_callback(msg)

        for url in start_urls:
            queue.append((self._normalise_url(url), 0))

        while queue and len(pages) < max_pages:
            url, depth = queue.popleft()

            if url in visited or depth > max_depth:
                continue
            visited.add(url)

            # Domain scope guard
            if same_domain and urlparse(url).netloc not in allowed_domains:
                continue

            # URL exclusion patterns
            if any(pat in url for pat in exclude_patterns):
                log(f"   ↳ Excluida (patrón): {url[:80]}")
                continue

            # robots.txt compliance
            if not self.is_allowed(url):
                log(f"⛔ Bloqueado por robots.txt: {url[:80]}")
                continue

            log(f"🌐 [{depth}/{max_depth}] {url[:90]}")

            html = self.fetch_page(url, use_js=use_js)
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")

            # Strip noise
            for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
                tag.decompose()

            title = soup.title.get_text(strip=True) if soup.title else ""
            text = soup.get_text(separator=" ", strip=True)
            # Collapse whitespace
            text = re.sub(r"\s{2,}", " ", text).strip()

            # Keyword filter — keep page if any keyword appears in title or body
            if keywords:
                combined = (title + " " + text).lower()
                if not any(kw.lower() in combined for kw in keywords):
                    log(f"   ↳ Sin keywords relevantes, descartada")
                    continue

            # Collect outgoing links for next depth level
            links: List[str] = []
            if depth < max_depth:
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    full = self._normalise_url(urljoin(url, href))
                    parsed = urlparse(full)
                    if parsed.scheme in ("http", "https") and full not in visited:
                        links.append(full)
                        queue.append((full, depth + 1))

            pages.append({
                "url": url,
                "title": title,
                "text": text[:60_000],
                "html": html[:120_000],
                "links": list(dict.fromkeys(links))[:100],
                "depth": depth,
                "crawled_at": datetime.now().isoformat(),
            })

            log(f"   ✅ '{title[:60]}' — {len(text):,} chars, {len(links)} links")

            time.sleep(self.delay)

        log(f"\n📦 Crawl finalizado: {len(pages)} páginas de {len(visited)} visitadas")
        return pages

    # ── Helpers ───────────────────────────────────────────────────

    @staticmethod
    def _normalise_url(url: str) -> str:
        """Remove fragment and trailing slash for dedup."""
        parsed = urlparse(url)
        clean = parsed._replace(fragment="")
        return clean.geturl().rstrip("/")

    @staticmethod
    def playwright_available() -> bool:
        return PLAYWRIGHT_AVAILABLE
