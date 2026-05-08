"""SQLite persistence layer for all web intelligence data."""
from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DB_PATH = Path("intelligence.db")

_SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ── crawl sessions ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS crawl_sessions (
    id           TEXT PRIMARY KEY,
    task_type    TEXT NOT NULL,
    query        TEXT,
    config       TEXT,                    -- JSON
    status       TEXT DEFAULT 'pending',
    created_at   TEXT,
    completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_sessions_type ON crawl_sessions(task_type);

-- ── raw pages ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS scraped_pages (
    id           TEXT PRIMARY KEY,
    session_id   TEXT NOT NULL,
    url          TEXT,
    title        TEXT,
    text_content TEXT,
    depth        INTEGER DEFAULT 0,
    crawled_at   TEXT,
    FOREIGN KEY (session_id) REFERENCES crawl_sessions(id)
);
CREATE INDEX IF NOT EXISTS idx_pages_session ON scraped_pages(session_id);
CREATE INDEX IF NOT EXISTS idx_pages_url     ON scraped_pages(url);

-- ── market intelligence ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS market_intelligence (
    id          TEXT PRIMARY KEY,
    session_id  TEXT NOT NULL,
    company     TEXT,
    url         TEXT,
    title       TEXT,
    products    TEXT,   -- JSON
    prices      TEXT,   -- JSON
    category    TEXT,
    detected_at TEXT,
    FOREIGN KEY (session_id) REFERENCES crawl_sessions(id)
);
CREATE INDEX IF NOT EXISTS idx_market_company  ON market_intelligence(company);
CREATE INDEX IF NOT EXISTS idx_market_category ON market_intelligence(category);
CREATE INDEX IF NOT EXISTS idx_market_session  ON market_intelligence(session_id);

-- ── leads ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS leads (
    id           TEXT PRIMARY KEY,
    session_id   TEXT NOT NULL,
    company      TEXT,
    contact_name TEXT,
    role         TEXT,
    email        TEXT,
    phone        TEXT,
    linkedin     TEXT,
    source_url   TEXT,
    sector       TEXT,
    country      TEXT,
    extracted_at TEXT,
    FOREIGN KEY (session_id) REFERENCES crawl_sessions(id)
);
CREATE INDEX IF NOT EXISTS idx_leads_email   ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_sector  ON leads(sector);
CREATE INDEX IF NOT EXISTS idx_leads_session ON leads(session_id);

-- ── content items ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS content_items (
    id           TEXT PRIMARY KEY,
    session_id   TEXT NOT NULL,
    source_url   TEXT,
    type         TEXT,
    title        TEXT,
    summary      TEXT,
    content      TEXT,
    author       TEXT,
    published_at TEXT,
    tags         TEXT,   -- JSON
    scraped_at   TEXT,
    FOREIGN KEY (session_id) REFERENCES crawl_sessions(id)
);
CREATE INDEX IF NOT EXISTS idx_content_type    ON content_items(type);
CREATE INDEX IF NOT EXISTS idx_content_session ON content_items(session_id);

-- ── monitoring targets ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS monitoring_targets (
    id           TEXT PRIMARY KEY,
    name         TEXT,
    url          TEXT,
    monitor_type TEXT,   -- price | product | content
    config       TEXT,   -- JSON (keywords, selectors, …)
    last_checked TEXT,
    is_active    INTEGER DEFAULT 1,
    created_at   TEXT
);

-- ── monitoring alerts ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS monitoring_alerts (
    id          TEXT PRIMARY KEY,
    target_id   TEXT NOT NULL,
    alert_type  TEXT,
    description TEXT,
    old_value   TEXT,
    new_value   TEXT,
    detected_at TEXT,
    FOREIGN KEY (target_id) REFERENCES monitoring_targets(id)
);
CREATE INDEX IF NOT EXISTS idx_alerts_target ON monitoring_alerts(target_id);
"""


class IntelligenceDB:
    """SQLite database manager for web intelligence pipeline."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    # ── Connection ─────────────────────────────────────────────────

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.executescript(_SCHEMA)

    # ── Crawl Sessions ─────────────────────────────────────────────

    def create_session(self, task_type: str, query: str, config: Dict) -> str:
        sid = str(uuid.uuid4())
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO crawl_sessions VALUES (?,?,?,?,?,?,?)",
                (sid, task_type, query, json.dumps(config, ensure_ascii=False),
                 "running", datetime.now().isoformat(), None),
            )
        return sid

    def complete_session(self, session_id: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE crawl_sessions SET status=?, completed_at=? WHERE id=?",
                ("completed", datetime.now().isoformat(), session_id),
            )

    def fail_session(self, session_id: str, error: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE crawl_sessions SET status=?, completed_at=? WHERE id=?",
                (f"failed: {error[:200]}", datetime.now().isoformat(), session_id),
            )

    def get_sessions(
        self, task_type: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            if task_type:
                rows = conn.execute(
                    "SELECT * FROM crawl_sessions WHERE task_type=? ORDER BY created_at DESC LIMIT ?",
                    (task_type, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM crawl_sessions ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [dict(r) for r in rows]

    # ── Scraped Pages ──────────────────────────────────────────────

    def save_page(self, session_id: str, page: Dict[str, Any]) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO scraped_pages VALUES (?,?,?,?,?,?,?)",
                (
                    str(uuid.uuid4()), session_id,
                    page.get("url"), page.get("title"),
                    (page.get("text") or "")[:10_000],
                    page.get("depth", 0), page.get("crawled_at"),
                ),
            )

    def get_pages(self, session_id: str) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM scraped_pages WHERE session_id=? ORDER BY crawled_at",
                (session_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ── Market Intelligence ────────────────────────────────────────

    def save_market_item(self, session_id: str, item: Dict[str, Any]) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO market_intelligence VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    str(uuid.uuid4()), session_id,
                    item.get("company"), item.get("url"), item.get("title"),
                    json.dumps(item.get("products", []), ensure_ascii=False),
                    json.dumps(item.get("prices", []), ensure_ascii=False),
                    item.get("category"),
                    item.get("crawled_at") or datetime.now().isoformat(),
                ),
            )

    def get_market_intel(
        self, company: Optional[str] = None, category: Optional[str] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM market_intelligence WHERE 1=1"
        params: List[Any] = []
        if company:
            sql += " AND company LIKE ?"
            params.append(f"%{company}%")
        if category:
            sql += " AND category=?"
            params.append(category)
        sql += " ORDER BY detected_at DESC LIMIT ?"
        params.append(limit)
        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["products"] = json.loads(d["products"] or "[]")
            d["prices"]   = json.loads(d["prices"]   or "[]")
            result.append(d)
        return result

    # ── Leads ──────────────────────────────────────────────────────

    def save_lead(self, session_id: str, lead: Dict[str, Any]) -> None:
        # Dedup by email
        if lead.get("email"):
            with self._conn() as conn:
                exists = conn.execute(
                    "SELECT id FROM leads WHERE email=?", (lead["email"],)
                ).fetchone()
                if exists:
                    return
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO leads VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    str(uuid.uuid4()), session_id,
                    lead.get("company"), lead.get("contact_name"),
                    lead.get("role"), lead.get("email"),
                    lead.get("phone"), lead.get("linkedin"),
                    lead.get("source_url"), lead.get("sector"),
                    lead.get("country"), datetime.now().isoformat(),
                ),
            )

    def get_leads(
        self, sector: Optional[str] = None, country: Optional[str] = None,
        limit: int = 500
    ) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM leads WHERE 1=1"
        params: List[Any] = []
        if sector:
            sql += " AND sector LIKE ?"
            params.append(f"%{sector}%")
        if country:
            sql += " AND country LIKE ?"
            params.append(f"%{country}%")
        sql += " ORDER BY extracted_at DESC LIMIT ?"
        params.append(limit)
        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    # ── Content Items ──────────────────────────────────────────────

    def save_content(self, session_id: str, item: Dict[str, Any]) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO content_items VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    str(uuid.uuid4()), session_id,
                    item.get("source_url"), item.get("type"),
                    item.get("title"), item.get("summary"),
                    (item.get("content") or "")[:6_000],
                    item.get("author"), item.get("published_at"),
                    json.dumps(item.get("tags", []), ensure_ascii=False),
                    item.get("scraped_at") or datetime.now().isoformat(),
                ),
            )

    def get_content(
        self, content_type: Optional[str] = None, limit: int = 200
    ) -> List[Dict[str, Any]]:
        if content_type:
            sql = "SELECT * FROM content_items WHERE type=? ORDER BY scraped_at DESC LIMIT ?"
            params: List[Any] = [content_type, limit]
        else:
            sql = "SELECT * FROM content_items ORDER BY scraped_at DESC LIMIT ?"
            params = [limit]
        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["tags"] = json.loads(d["tags"] or "[]")
            result.append(d)
        return result

    # ── Monitoring ─────────────────────────────────────────────────

    def save_monitoring_target(
        self, name: str, url: str, monitor_type: str, config: Dict
    ) -> str:
        tid = str(uuid.uuid4())
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO monitoring_targets VALUES (?,?,?,?,?,?,?,?)",
                (tid, name, url, monitor_type, json.dumps(config, ensure_ascii=False),
                 None, 1, datetime.now().isoformat()),
            )
        return tid

    def get_monitoring_targets(self, active_only: bool = True) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM monitoring_targets"
        if active_only:
            sql += " WHERE is_active=1"
        with self._conn() as conn:
            rows = conn.execute(sql).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["config"] = json.loads(d["config"] or "{}")
            result.append(d)
        return result

    def deactivate_monitoring_target(self, target_id: str) -> None:
        with self._conn() as conn:
            conn.execute("UPDATE monitoring_targets SET is_active=0 WHERE id=?", (target_id,))

    def save_alert(
        self, target_id: str, alert_type: str, description: str,
        old_value: str = "", new_value: str = ""
    ) -> str:
        aid = str(uuid.uuid4())
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO monitoring_alerts VALUES (?,?,?,?,?,?,?)",
                (aid, target_id, alert_type, description,
                 old_value, new_value, datetime.now().isoformat()),
            )
        return aid

    def get_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT a.*, t.name AS target_name, t.url AS target_url
                   FROM monitoring_alerts a
                   LEFT JOIN monitoring_targets t ON a.target_id = t.id
                   ORDER BY a.detected_at DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ── Stats & Export ─────────────────────────────────────────────

    def get_stats(self) -> Dict[str, int]:
        tables = [
            "crawl_sessions", "scraped_pages", "market_intelligence",
            "leads", "content_items", "monitoring_targets", "monitoring_alerts",
        ]
        stats: Dict[str, int] = {}
        with self._conn() as conn:
            for table in tables:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                stats[table] = count
        return stats

    _ALLOWED_EXPORT = frozenset(
        {"leads", "market_intelligence", "content_items",
         "crawl_sessions", "scraped_pages", "monitoring_alerts"}
    )

    def export_json(self, table: str, limit: int = 2000) -> str:
        if table not in self._ALLOWED_EXPORT:
            return "[]"
        with self._conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT ?", (limit,)
            ).fetchall()
        return json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2)


# ── Singleton ─────────────────────────────────────────────────────────────────
intelligence_db = IntelligenceDB()
