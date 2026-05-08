from __future__ import annotations

import json
import re
import time
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

DATE_PATTERN = re.compile(
    r"\b(20\d{2}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]20\d{2})\b"
)


@dataclass
class PageRecord:
    url: str
    status_code: int
    title: str
    h1: List[str]
    h2: List[str]
    text_excerpt: str
    possible_dates: List[str]
    out_links: List[str]


class DeepWebScraper:
    def __init__(self, timeout: int = 20, delay_seconds: float = 0.35) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"})
        self.timeout = timeout
        self.delay_seconds = delay_seconds

    def crawl(self, seed_url: str, max_pages: int = 20) -> Dict:
        domain = urlparse(seed_url).netloc
        queue: deque[str] = deque([seed_url])
        visited: Set[str] = set()
        pages: List[PageRecord] = []
        errors: List[Dict] = []

        while queue and len(visited) < max_pages:
            url = queue.popleft()
            url = self._normalize_url(url)
            if not url or url in visited:
                continue
            if urlparse(url).netloc != domain:
                continue

            visited.add(url)
            try:
                response = self.session.get(url, timeout=self.timeout)
                ctype = response.headers.get("content-type", "")
                if "text/html" not in ctype:
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                page = self._extract_page_data(url, response.status_code, soup)
                pages.append(page)

                for link in page.out_links:
                    normalized = self._normalize_url(link)
                    if not normalized:
                        continue
                    if urlparse(normalized).netloc == domain and normalized not in visited:
                        queue.append(normalized)

                time.sleep(self.delay_seconds)
            except Exception as exc:
                errors.append({"url": url, "error": str(exc)})

        return {
            "seed_url": seed_url,
            "domain": domain,
            "crawled_at": datetime.now().isoformat(),
            "max_pages_requested": max_pages,
            "pages_crawled": len(pages),
            "visited_urls": sorted(visited),
            "pages": [asdict(p) for p in pages],
            "errors": errors,
        }

    def _extract_page_data(self, url: str, status_code: int, soup: BeautifulSoup) -> PageRecord:
        title = (soup.title.string or "").strip() if soup.title and soup.title.string else ""
        h1 = [x.get_text(" ", strip=True) for x in soup.find_all("h1")][:6]
        h2 = [x.get_text(" ", strip=True) for x in soup.find_all("h2")][:12]

        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()

        text = soup.get_text(" ", strip=True)
        text = re.sub(r"\s+", " ", text)
        excerpt = text[:2200]

        raw_links = []
        for a in soup.find_all("a", href=True):
            raw_links.append(urljoin(url, a["href"]))

        dates = sorted(set(DATE_PATTERN.findall(text)))[:15]

        return PageRecord(
            url=url,
            status_code=status_code,
            title=title,
            h1=h1,
            h2=h2,
            text_excerpt=excerpt,
            possible_dates=dates,
            out_links=sorted(set(raw_links))[:120],
        )

    @staticmethod
    def _normalize_url(url: str) -> str:
        if not url:
            return ""
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return ""
        cleaned = parsed._replace(fragment="")
        normalized = cleaned.geturl()
        if normalized.endswith("/"):
            return normalized[:-1]
        return normalized


def build_combined_summary(scrape_data: Dict[str, Dict]) -> Dict:
    def collect_keywords(pages: List[Dict], patterns: List[str], max_items: int = 20) -> List[str]:
        hits: List[str] = []
        regex = re.compile("|".join(patterns), re.IGNORECASE)
        for page in pages:
            blob = " ".join([page.get("title", ""), " ".join(page.get("h1", [])), " ".join(page.get("h2", [])), page.get("text_excerpt", "")])
            if regex.search(blob):
                hits.append(page.get("url", ""))
            if len(hits) >= max_items:
                break
        return hits

    ing_pages = scrape_data["ingecart"].get("pages", [])
    fespa_pages = scrape_data["fespa"].get("pages", [])
    iar_pages = scrape_data["iar"].get("pages", [])

    combined = {
        "generated_at": datetime.now().isoformat(),
        "stats": {
            "ingecart_pages": scrape_data["ingecart"].get("pages_crawled", 0),
            "fespa_pages": scrape_data["fespa"].get("pages_crawled", 0),
            "iar_pages": scrape_data["iar"].get("pages_crawled", 0),
        },
        "ingecart_signals": {
            "automation_and_robotics_pages": collect_keywords(ing_pages, [r"robot", r"automat", r"industr", r"corrugat", r"packaging"]),
            "innovation_pages": collect_keywords(ing_pages, [r"innov", r"digital", r"ai", r"intelig", r"soluci"]),
        },
        "fespa_signals": {
            "exhibit_related_pages": collect_keywords(fespa_pages, [r"exhibit", r"expo", r"show", r"event", r"stand"]),
            "industry_trend_pages": collect_keywords(fespa_pages, [r"digital", r"automation", r"industry", r"technology", r"innovation"]),
        },
        "iar_signals": {
            "latest_information_pages": collect_keywords(iar_pages, [r"news", r"noticia", r"blog", r"release", r"update", r"novedad", r"ia"]),
            "ai_value_pages": collect_keywords(iar_pages, [r"ai", r"intelig", r"agent", r"automat", r"digital", r"data"]),
        },
    }

    return combined


def write_markdown_report(output_dir: Path, scrape_data: Dict[str, Dict], summary: Dict) -> Path:
    ts = datetime.now().strftime("%Y-%m-%d")
    report_path = output_dir / f"INGECART_FESPA_IAR_DEEP_REPORT_{ts}.md"

    def top_titles(dataset: Dict, n: int = 8) -> List[str]:
        titles = []
        for p in dataset.get("pages", []):
            title = p.get("title", "").strip()
            if title:
                titles.append(f"- {title} | {p.get('url', '')}")
            if len(titles) >= n:
                break
        return titles

    content = []
    content.append("# Deep Intelligence Report: Ingecart + FESPA + IAR")
    content.append("")
    content.append(f"Date: {datetime.now().isoformat()}")
    content.append("Scope: Deep crawl and strategic synthesis")
    content.append("")
    content.append("## 1) Crawl Coverage")
    content.append(f"- Ingecart pages crawled: {summary['stats']['ingecart_pages']}")
    content.append(f"- FESPA pages crawled: {summary['stats']['fespa_pages']}")
    content.append(f"- IAR pages crawled: {summary['stats']['iar_pages']}")
    content.append("")

    content.append("## 2) Ingecart Highlights (fresh signals)")
    content.extend(top_titles(scrape_data["ingecart"]))
    content.append("")

    content.append("## 3) FESPA Exhibit/Market Signals")
    content.extend(top_titles(scrape_data["fespa"]))
    content.append("")

    content.append("## 4) IAR Latest Information Signals")
    content.extend(top_titles(scrape_data["iar"]))
    content.append("")

    content.append("## 5) Strategic Joint Value: IAR + Ingecart at FESPA")
    content.append("- Positioning: combine industrial engineering credibility (Ingecart) with AI/software intelligence and digital tooling (IAR).")
    content.append("- Demo narrative: from plant data capture to AI-agent recommendations and operator-facing actions.")
    content.append("- Public proof points: show measurable KPIs (downtime reduction, scrap reduction, energy efficiency, maintenance predictability).")
    content.append("- Booth architecture: live digital twin dashboard, agent copilot for plant teams, and workflow automation for quality/maintenance.")
    content.append("- Commercial impact: faster qualification of leads, stronger differentiation, and clearer ROI story for industrial buyers.")
    content.append("")

    content.append("## 6) Recommended Public Message")
    content.append("Ingecart and IAR jointly deliver next-generation industrial solutions where automation, AI agents, and digital tools improve productivity, sustainability, and decision quality in real production environments.")
    content.append("")

    report_path.write_text("\n".join(content), encoding="utf-8")
    return report_path


def main() -> None:
    root = Path(__file__).resolve().parent
    ts = datetime.now().strftime("%Y-%m-%d")

    scraper = DeepWebScraper()

    targets = {
        "ingecart": ("https://www.ingecart.eu/", 35),
        "fespa": ("https://europe.fespa.com/es/exhibit", 25),
        "iar": ("https://www.iar-soft.com/ia", 25),
    }

    all_data: Dict[str, Dict] = {}
    for name, (url, max_pages) in targets.items():
        print(f"[crawl] {name}: {url} (max_pages={max_pages})")
        all_data[name] = scraper.crawl(url, max_pages=max_pages)

    deep_json = root / f"ingecart_fespa_iar_deep_data_{ts}.json"
    deep_json.write_text(json.dumps(all_data, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = build_combined_summary(all_data)
    summary_json = root / f"ingecart_fespa_iar_summary_{ts}.json"
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    report_path = write_markdown_report(root, all_data, summary)

    print(f"[ok] data: {deep_json}")
    print(f"[ok] summary: {summary_json}")
    print(f"[ok] report: {report_path}")


if __name__ == "__main__":
    main()
