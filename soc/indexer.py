from __future__ import annotations

import os
import time
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional


DEFAULT_DB = Path('.data') / 'soc.db'


class Indexer:
    def __init__(self, db_path: Optional[Path] = None, companies: Optional[Dict[str, str]] = None):
        self.db_path = Path(db_path or DEFAULT_DB)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.companies = companies or {}
        self._init_db()

    def _conn(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._conn()
        c = conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY,
            company TEXT,
            file_path TEXT UNIQUE,
            file_name TEXT,
            last_modified REAL,
            content TEXT,
            summary TEXT,
            status TEXT,
            version INTEGER,
            inserted_at REAL
        )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_company_status ON documents(company,status)')
        conn.commit()
        conn.close()

    def extract_text(self, path: Path) -> str:
        try:
            if path.suffix.lower() in ('.md', '.txt', '.py', '.json', '.yaml', '.yml', '.html', '.htm', '.csv'):
                return path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return ""
        return ""

    def _summarize(self, text: str, n_lines: int = 6) -> str:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if not lines:
            return ""
        return '\n'.join(lines[:n_lines])

    def _upsert_doc(self, company: str, file_path: str, content: str, mtime: float):
        conn = self._conn()
        c = conn.cursor()
        file_name = Path(file_path).name
        now = time.time()
        c.execute('SELECT id, last_modified, version FROM documents WHERE file_path=?', (file_path,))
        row = c.fetchone()
        if row:
            existing_mtime = row['last_modified']
            if mtime > existing_mtime:
                # mark old as superseded
                c.execute('UPDATE documents SET status=? WHERE id=?', ('superseded', row['id']))
                version = (row['version'] or 1) + 1
                summary = self._summarize(content)
                c.execute(
                    'INSERT INTO documents (company,file_path,file_name,last_modified,content,summary,status,version,inserted_at) VALUES (?,?,?,?,?,?,?,?,?)',
                    (company, file_path, file_name, mtime, content, summary, 'current', version, now),
                )
        else:
            summary = self._summarize(content)
            c.execute(
                'INSERT INTO documents (company,file_path,file_name,last_modified,content,summary,status,version,inserted_at) VALUES (?,?,?,?,?,?,?,?,?)',
                (company, file_path, file_name, mtime, content, summary, 'current', 1, now),
            )
        conn.commit()
        conn.close()

    def index_path(self, company: str, root_path: str, recursive: bool = True) -> int:
        root = Path(root_path)
        if not root.exists():
            return 0
        count = 0
        iterator = root.rglob('*') if recursive else root.iterdir()
        for p in iterator:
            if not p.is_file():
                continue
            if p.suffix.lower() not in ('.md', '.txt', '.py', '.json', '.yaml', '.yml', '.html', '.htm', '.csv'):
                continue
            try:
                content = self.extract_text(p)
                mtime = p.stat().st_mtime
                self._upsert_doc(company, str(p.resolve()), content, mtime)
                count += 1
            except Exception:
                continue
        return count

    def index_all(self) -> int:
        total = 0
        for company, path in self.companies.items():
            total += self.index_path(company, path)
        return total
