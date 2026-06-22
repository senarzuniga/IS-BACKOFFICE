import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from .base_agent import BaseAgent
from .utils.scraper import scrape_page
from .utils.news_fetcher import fetch_news
from .utils.cache import SQLiteCache

logger = logging.getLogger(__name__)


class MarketIntelligenceAgent(BaseAgent):
    def __init__(self, model: Optional[str] = None, cache_path: Optional[str] = None):
        super().__init__(model=model)
        root = Path(__file__).resolve().parents[3]
        default_cache = os.path.join(root, "data", "competitive_intelligence", "cache.db")
        self.cache = SQLiteCache(cache_path or default_cache)

    def _load_local_evidence(self) -> List[Dict[str, Any]]:
        root = Path(__file__).resolve().parents[3]
        data_dir = root / "data" / "competitive_intelligence"
        items = []
        if data_dir.exists():
            for p in data_dir.rglob("*.json"):
                try:
                    with open(p, "r", encoding="utf-8") as fh:
                        j = json.load(fh)
                        items.append({"source": str(p), "text": json.dumps(j)[:2000]})
                except Exception:
                    continue
        return items

    def run(self, company: str, seeds: Optional[List[str]] = None, no_web: bool = False) -> Dict[str, Any]:
        seeds = seeds or []
        evidence: List[Dict[str, Any]] = []

        # local evidence
        evidence.extend(self._load_local_evidence())

        # web scraping
        if not no_web and seeds:
            for s in seeds:
                key = f"scrape:{s}"
                cached = self.cache.get(key, ttl=24 * 3600)
                if cached:
                    evidence.append({"source": s, "text": cached.get("snippets", [])})
                    continue
                out = scrape_page(s)
                self.cache.set(key, out)
                evidence.append({"source": s, "text": out.get("snippets", [])})

        # news
        news = []
        try:
            news = fetch_news(company)
        except Exception:
            news = []
        if news:
            evidence.append({"source": "newsapi", "text": str(news[:8])})

        # Build prompt for extraction
        prompt_lines = [f"Evidence items: {len(evidence)}"]
        for e in evidence[:10]:
            prompt_lines.append(f"SOURCE: {e.get('source')}\nSNIPPET: {e.get('text')}")

        system = {"role": "system", "content": "You are a factual extractor. Do not invent numbers. If missing, return 'No disponible en fuentes públicas'. Return JSON."}
        user = {"role": "user", "content": "\n".join(prompt_lines) + f"\n\nExtract company profile for {company} in JSON with fields: company, description, products, markets, estimated_revenue, employees, tech_signals, news_signals, positioning, uncertainties, sources."}

        result = self.call_llm_json([system, user], temperature=0)
        # if LLM returned raw, build simple fallback
        if isinstance(result, dict) and result.get("_raw"):
            # fallback: use baseline if available
            root = Path(__file__).resolve().parents[3]
            baseline = root / "data" / "competitive_intelligence" / "ingecart_baseline.json"
            fallback = {"company": company, "description": "No disponible en fuentes públicas", "products": [], "markets": [], "estimated_revenue": "No disponible en fuentes públicas", "employees": "No disponible in sources", "tech_signals": [], "news_signals": [], "positioning": "No disponible", "uncertainties": [], "sources": []}
            if baseline.exists():
                try:
                    with open(baseline, "r", encoding="utf-8") as fh:
                        b = json.load(fh)
                        fallback.update({k: b.get(k, fallback.get(k)) for k in fallback.keys()})
                except Exception:
                    pass
            return fallback

        return result
