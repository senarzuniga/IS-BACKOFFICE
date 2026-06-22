import logging
from typing import Dict, Any, List
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


def extract_text_and_snippets(html: str) -> Dict[str, Any]:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    paragraphs = [p.get_text(separator=" ", strip=True) for p in soup.find_all("p")]
    text = "\n\n".join(paragraphs)
    snippets: List[str] = []
    for p in paragraphs:
        if len(p) > 80:
            snippets.append(p[:800])
        if len(snippets) >= 6:
            break
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
            continue
        try:
            full = urljoin("", href)
            links.append(full)
        except Exception:
            continue
    return {"title": title, "text": text, "snippets": snippets, "links": links}


def scrape_page(url: str, timeout: int = 12, use_playwright: bool = True) -> Dict[str, Any]:
    """Scrape a page using Playwright when available, otherwise fallback to requests+bs4.

    Returns a dict with keys: url, title, text, snippets, links
    """
    if use_playwright:
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
                html = page.content()
                browser.close()
                out = extract_text_and_snippets(html)
                out["url"] = url
                return out
        except Exception as e:
            logger.debug("playwright scrape failed %s: %s", url, e)

    # fallback
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {"User-Agent": "IngecartScraper/1.0"}
        r = requests.get(url, timeout=timeout, headers=headers)
        r.raise_for_status()
        html = r.text
        out = extract_text_and_snippets(html)
        out["url"] = url
        return out
    except Exception as e:
        logger.debug("requests scrape failed %s: %s", url, e)
        return {"url": url, "title": "", "text": "", "snippets": [], "links": []}
