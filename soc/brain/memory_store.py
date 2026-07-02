from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional


DEFAULT_DB = Path('.data') / 'enterprise_memory.db'


class MemoryStore:
    """Persistent Enterprise Memory using SQLite.

    The store contains tables for companies, documents and other business
    entities. Each record includes a UUID and required metadata.
    """

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
        # Companies
        cur.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            uuid TEXT PRIMARY KEY,
            name TEXT UNIQUE,
            created_at REAL,
            updated_at REAL,
            source_ref TEXT,
            confidence REAL,
            owner TEXT,
            status TEXT,
            version INTEGER,
            meta TEXT
        )
        ''')

        # Documents (general-purpose)
        cur.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            uuid TEXT PRIMARY KEY,
            company_uuid TEXT,
            file_name TEXT,
            file_path TEXT,
            source_ref TEXT,
            created_at REAL,
            updated_at REAL,
            last_modified REAL,
            confidence REAL,
            owner TEXT,
            status TEXT,
            version INTEGER,
            content TEXT,
            summary TEXT,
            meta TEXT
        )
        ''')

        # Basic entity tables (decisions, risks, events, ai_queries, sources)
        cur.execute('''
        CREATE TABLE IF NOT EXISTS decisions (
            uuid TEXT PRIMARY KEY,
            company_uuid TEXT,
            title TEXT,
            content TEXT,
            created_at REAL,
            updated_at REAL,
            source_ref TEXT,
            confidence REAL,
            owner TEXT,
            status TEXT,
            version INTEGER,
            meta TEXT
        )
        ''')

        cur.execute('''
        CREATE TABLE IF NOT EXISTS risks (
            uuid TEXT PRIMARY KEY,
            company_uuid TEXT,
            title TEXT,
            description TEXT,
            severity REAL,
            probability REAL,
            created_at REAL,
            updated_at REAL,
            meta TEXT
        )
        ''')

        cur.execute('''
        CREATE TABLE IF NOT EXISTS ai_queries (
            uuid TEXT PRIMARY KEY,
            company_uuid TEXT,
            question TEXT,
            response TEXT,
            created_at REAL,
            meta TEXT
        )
        ''')

        cur.execute('CREATE INDEX IF NOT EXISTS idx_docs_company ON documents(company_uuid)')
        conn.commit()
        conn.close()

    # Companies
    def add_company(self, name: str, source_ref: Optional[str] = None, owner: Optional[str] = None, confidence: float = 0.8, status: str = 'active') -> str:
        u = str(uuid.uuid4())
        now = time.time()
        conn = self._conn()
        cur = conn.cursor()
        cur.execute('INSERT INTO companies (uuid,name,created_at,updated_at,source_ref,confidence,owner,status,version,meta) VALUES (?,?,?,?,?,?,?,?,?,?)', (u, name, now, now, source_ref, confidence, owner, status, 1, json.dumps({})))
        conn.commit()
        conn.close()
        return u

    def get_company_by_name(self, name: str) -> Optional[Dict]:
        conn = self._conn()
        cur = conn.cursor()
        cur.execute('SELECT * FROM companies WHERE name=?', (name,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return dict(row)

    # Documents
    def add_document(self, company_uuid: str, file_name: str, content: str, file_path: Optional[str] = None, source_ref: Optional[str] = None, confidence: float = 0.8, owner: Optional[str] = None, status: str = 'current', version: int = 1, summary: Optional[str] = None, meta: Optional[Dict] = None) -> str:
        u = str(uuid.uuid4())
        now = time.time()
        summary = summary or (content or '')[:1000]
        conn = self._conn()
        cur = conn.cursor()
        cur.execute('INSERT INTO documents (uuid,company_uuid,file_name,file_path,source_ref,created_at,updated_at,last_modified,confidence,owner,status,version,content,summary,meta) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (u, company_uuid, file_name, file_path, source_ref, now, now, now, confidence, owner, status, version, content, summary, json.dumps(meta or {})))
        conn.commit()
        conn.close()
        return u

    def get_document(self, uuid_str: str) -> Optional[Dict]:
        conn = self._conn()
        cur = conn.cursor()
        cur.execute('SELECT * FROM documents WHERE uuid=?', (uuid_str,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def search_documents(self, company_uuid: Optional[str] = None, query: Optional[str] = None, limit: int = 10) -> List[Dict]:
        conn = self._conn()
        cur = conn.cursor()
        params = []
        sql = 'SELECT * FROM documents'
        clauses = []
        if company_uuid:
            clauses.append('company_uuid=?')
            params.append(company_uuid)
        if query:
            clauses.append('(content LIKE ? OR file_name LIKE ? OR summary LIKE ?)')
            qlike = f'%{query}%'
            params.extend([qlike, qlike, qlike])
        if clauses:
            sql += ' WHERE ' + ' AND '.join(clauses)
        sql += ' ORDER BY last_modified DESC LIMIT ?'
        params.append(limit)
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # Decisions
    def add_decision(self, company_uuid: str, title: str, content: str, source_ref: Optional[str] = None, owner: Optional[str] = None, confidence: float = 0.8) -> str:
        u = str(uuid.uuid4())
        now = time.time()
        conn = self._conn()
        cur = conn.cursor()
        cur.execute('INSERT INTO decisions (uuid,company_uuid,title,content,created_at,updated_at,source_ref,confidence,owner,status,version,meta) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (u, company_uuid, title, content, now, now, source_ref, confidence, owner, 'accepted', 1, json.dumps({})))
        conn.commit()
        conn.close()
        return u

    def add_risk(self, company_uuid: str, title: str, description: str, severity: float = 0.5, probability: float = 0.5, meta: Optional[Dict] = None) -> str:
        u = str(uuid.uuid4())
        now = time.time()
        conn = self._conn()
        cur = conn.cursor()
        cur.execute('INSERT INTO risks (uuid,company_uuid,title,description,severity,probability,created_at,updated_at,meta) VALUES (?,?,?,?,?,?,?,?,?)', (u, company_uuid, title, description, severity, probability, now, now, json.dumps(meta or {})))
        conn.commit()
        conn.close()
        return u

    def record_ai_query(self, company_uuid: str, question: str, response: str, meta: Optional[Dict] = None) -> str:
        u = str(uuid.uuid4())
        now = time.time()
        conn = self._conn()
        cur = conn.cursor()
        cur.execute('INSERT INTO ai_queries (uuid,company_uuid,question,response,created_at,meta) VALUES (?,?,?,?,?,?)', (u, company_uuid, question, response, now, json.dumps(meta or {})))
        conn.commit()
        conn.close()
        return u
