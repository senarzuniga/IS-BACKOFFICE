"""Full intelligence pipeline: crawl → extract → store."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .crawler import IntelligenceCrawler
from .extractors import ContentExtractor, LeadExtractor, MarketExtractor
from .storage import IntelligenceDB, intelligence_db

logger = logging.getLogger(__name__)

TASK_TYPES: Dict[str, str] = {
    "market_intel":  "Inteligencia de Mercado y Competencia",
    "leads":         "Generación de Leads B2B",
    "content":       "Agregación de Contenido",
    "research":      "Investigación y Análisis",
    "monitoring":    "Monitorización Automática",
    "operational":   "Automatización Operativa",
}

# Which extractors run for each task type
_TASK_EXTRACTORS: Dict[str, List[str]] = {
    "market_intel": ["market", "content"],
    "leads":        ["leads"],
    "content":      ["content"],
    "research":     ["market", "content", "leads"],
    "monitoring":   ["market", "content"],
    "operational":  ["market", "leads"],
}


class IntelligencePipeline:
    """
    Orchestrates the full intelligence pipeline.

    Steps:
        1. Crawl URLs (BFS, multi-level, optional JS rendering).
        2. Extract structured data per task type.
        3. Persist everything to SQLite.

    Thread-safe: uses module-level crawler/extractor singletons.
    """

    def __init__(self, db: IntelligenceDB = intelligence_db):
        self.db        = db
        self.crawler   = IntelligenceCrawler()
        self.market_ex = MarketExtractor()
        self.lead_ex   = LeadExtractor()
        self.content_ex = ContentExtractor()

    def run(
        self,
        task_type:         str,
        query:             str,
        start_urls:        List[str],
        max_pages:         int = 30,
        max_depth:         int = 2,
        use_js:            bool = False,
        keywords:          Optional[List[str]] = None,
        exclude_patterns:  Optional[List[str]] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Execute the pipeline and return a summary dict.

        Returns:
            {session_id, status, counts, query, task_type, started_at, completed_at}
        """
        if task_type not in TASK_TYPES:
            raise ValueError(f"Unknown task_type '{task_type}'. Valid: {list(TASK_TYPES)}")

        def log(msg: str) -> None:
            logger.info(msg)
            if progress_callback:
                progress_callback(msg)

        started_at = datetime.now().isoformat()
        log(f"🚀 [{task_type}] {TASK_TYPES[task_type]}")
        log(f"   Query: {query!r}  |  URLs: {len(start_urls)}  |  max_pages={max_pages}  |  depth={max_depth}  |  JS={use_js}")

        config = {
            "query": query,
            "start_urls": start_urls,
            "max_pages": max_pages,
            "max_depth": max_depth,
            "use_js": use_js,
            "keywords": keywords or [],
        }
        session_id = self.db.create_session(task_type, query, config)

        try:
            # ── Step 1: Crawl ──────────────────────────────────────
            log("🌐 Paso 1/3: Deep crawling...")
            pages = self.crawler.crawl(
                start_urls=start_urls,
                max_pages=max_pages,
                max_depth=max_depth,
                use_js=use_js,
                keywords=keywords,
                exclude_patterns=exclude_patterns,
                progress_callback=log,
            )
            log(f"   📦 {len(pages)} páginas obtenidas")

            for page in pages:
                self.db.save_page(session_id, page)

            # ── Step 2: Extract ────────────────────────────────────
            log("🔍 Paso 2/3: Extrayendo inteligencia estructurada...")
            counts = {
                "pages":   len(pages),
                "market":  0,
                "leads":   0,
                "content": 0,
            }
            active_extractors = _TASK_EXTRACTORS.get(task_type, ["market", "content"])

            for page in pages:
                if "market" in active_extractors:
                    item = self.market_ex.extract(page)
                    if item.get("prices") or item.get("products"):
                        self.db.save_market_item(session_id, item)
                        counts["market"] += 1

                if "leads" in active_extractors:
                    for lead in self.lead_ex.extract(page):
                        if lead.get("email") or lead.get("phone") or lead.get("linkedin"):
                            self.db.save_lead(session_id, lead)
                            counts["leads"] += 1

                if "content" in active_extractors:
                    item = self.content_ex.extract(page)
                    if item:
                        self.db.save_content(session_id, item)
                        counts["content"] += 1

            log(
                f"   ✅ Market: {counts['market']} | "
                f"Leads: {counts['leads']} | "
                f"Content: {counts['content']}"
            )

            # ── Step 3: Persist & complete ─────────────────────────
            self.db.complete_session(session_id)
            completed_at = datetime.now().isoformat()
            log(f"💾 Paso 3/3: Almacenado en DB. Sesión: {session_id[:8]}…")

            return {
                "session_id":   session_id,
                "status":       "completed",
                "counts":       counts,
                "query":        query,
                "task_type":    task_type,
                "started_at":   started_at,
                "completed_at": completed_at,
            }

        except Exception as exc:
            self.db.fail_session(session_id, str(exc))
            log(f"❌ Error en pipeline: {exc}")
            raise

    # ── Monitoring run ─────────────────────────────────────────────

    def run_monitoring_check(
        self,
        target: Dict[str, Any],
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Crawl a monitoring target and compare with previous data.
        Returns a list of alert dicts if changes are detected.
        """
        url  = target["url"]
        name = target["name"]
        mtype = target.get("monitor_type", "content")
        config = target.get("config", {})

        def log(msg: str) -> None:
            logger.info(msg)
            if progress_callback:
                progress_callback(msg)

        log(f"👁️ Monitorizando: {name} ({url})")

        pages = self.crawler.crawl(
            start_urls=[url],
            max_pages=config.get("max_pages", 5),
            max_depth=config.get("max_depth", 1),
            use_js=False,
        )

        alerts: List[Dict[str, Any]] = []
        for page in pages:
            if mtype == "price":
                item = self.market_ex.extract(page)
                prices = item.get("prices", [])
                # Compare with stored
                prev = self.db.get_market_intel(company=item.get("company"), limit=1)
                if prev:
                    old_prices = prev[0].get("prices", [])
                    if set(prices) != set(old_prices):
                        aid = self.db.save_alert(
                            target_id=target["id"],
                            alert_type="price_change",
                            description=f"Cambio de precios en {url}",
                            old_value=str(old_prices),
                            new_value=str(prices),
                        )
                        alerts.append({"alert_id": aid, "type": "price_change", "url": url})
                        log(f"🔔 Alerta precio detectada: {url}")
                self.db.save_market_item(target["id"], item)

            elif mtype == "content":
                content = self.content_ex.extract(page)
                if content:
                    existing = [
                        c for c in self.db.get_content(limit=200)
                        if c["source_url"] == url
                    ]
                    if not existing:
                        self.db.save_content(target["id"], content)
                        aid = self.db.save_alert(
                            target_id=target["id"],
                            alert_type="new_content",
                            description=f"Nuevo contenido: {content.get('title', url)}",
                            new_value=content.get("title", ""),
                        )
                        alerts.append({"alert_id": aid, "type": "new_content", "url": url})
                        log(f"🔔 Nuevo contenido: {content.get('title', '')}")

        return alerts


# ── Singleton ─────────────────────────────────────────────────────────────────
pipeline = IntelligencePipeline()
