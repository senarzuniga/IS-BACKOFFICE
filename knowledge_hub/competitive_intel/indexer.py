"""Indexer skeleton for Competitive Intelligence (SQLite-backed).

This indexer provides safe, local storage of companies, sources and
documents. It does NOT execute any crawling or scraping on import.
All ingestion must be invoked explicitly by calling methods.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Optional, List, Dict


DEFAULT_DB = Path('.data') / 'ci.db'


class Indexer:
    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = Path(db_path) if db_path else DEFAULT_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._conn()
        cur = conn.cursor()
        cur.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            seed_url TEXT,
            meta TEXT
        )
        ''')
        cur.execute('''
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY,
            company_id INTEGER,
            url TEXT,
            type TEXT,
            discovered_at REAL
        )
        ''')
        cur.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY,
            company_id INTEGER,
            source_id INTEGER,
            file_name TEXT,
            file_path TEXT,
            url TEXT,
            last_modified REAL,
            content TEXT,
            summary TEXT,
            status TEXT,
            version INTEGER,
            meta TEXT
        )
        ''')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_company_documents ON documents(company_id)')
        conn.commit()
        conn.close()

    def add_company(self, name: str, seed_url: Optional[str] = None, meta: Optional[Dict] = None) -> int:
        conn = self._conn()
        cur = conn.cursor()
        cur.execute('INSERT OR IGNORE INTO companies (name, seed_url, meta) VALUES (?,?,?)', (name, seed_url, json.dumps(meta or {})))
        conn.commit()
        cur.execute('SELECT id FROM companies WHERE name=?', (name,))
        row = cur.fetchone()
        conn.close()
        return int(row['id'])

    def add_source(self, company_id: int, url: str, type: str = 'web') -> int:
        conn = self._conn()
        cur = conn.cursor()
        now = time.time()
        cur.execute('INSERT INTO sources (company_id, url, type, discovered_at) VALUES (?,?,?,?)', (company_id, url, type, now))
        conn.commit()
        rid = cur.lastrowid
        conn.close()
        return int(rid)

    def add_document(self, company_id: int, source_id: int, file_name: str, content: str, file_path: Optional[str] = None, url: Optional[str] = None, meta: Optional[Dict] = None) -> int:
        conn = self._conn()
        cur = conn.cursor()
        now = time.time()
        summary = (content or '')[:1000]
        cur.execute('INSERT INTO documents (company_id, source_id, file_name, file_path, url, last_modified, content, summary, status, version, meta) VALUES (?,?,?,?,?,?,?,?,?,?,?)', (company_id, source_id, file_name, file_path, url, now, content, summary, 'current', 1, json.dumps(meta or {})))
        conn.commit()
        rid = cur.lastrowid
        conn.close()
        return int(rid)

    def search_by_company_name(self, company_name: str, query: str, limit: int = 10) -> List[Dict]:
        conn = self._conn()
        cur = conn.cursor()
        cur.execute('SELECT id FROM companies WHERE name=?', (company_name,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return []
        cid = row['id']
        tokens = [t.lower() for t in query.strip().split() if t.strip()]
        cur.execute('SELECT id,file_name,file_path,last_modified,summary,content FROM documents WHERE company_id=? AND status=?', (cid, 'current'))
        rows = cur.fetchall()
        if not rows:
            conn.close()
            return []
        min_m = min(r['last_modified'] for r in rows)
        max_m = max(r['last_modified'] for r in rows)

        results = []
        for r in rows:
            content = (r['content'] or '').lower()
            relevance = sum(content.count(t) for t in tokens) if tokens else 0
            rel_norm = min(relevance, 20) / 20.0
            if max_m > min_m:
                recency = (r['last_modified'] - min_m) / (max_m - min_m)
            else:
                recency = 1.0
            score = 0.7 * recency + 0.3 * rel_norm
            summary = r['summary'] or ((r['content'] or '')[:300])
            results.append({'file': r['file_name'], 'path': r['file_path'], 'last_modified': r['last_modified'], 'summary': summary, 'confidence': round(min(1.0, score), 2), 'score_raw': score})

        results = sorted(results, key=lambda x: x['score_raw'], reverse=True)[:limit]
        conn.close()
        return results
