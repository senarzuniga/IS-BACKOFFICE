import os
import sqlite3
import json
import time
from typing import Optional, Any


class SQLiteCache:
    def __init__(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT,
                created_at REAL
            )
            """
        )
        self.conn.commit()

    def get(self, key: str, ttl: Optional[int] = None) -> Optional[Any]:
        cur = self.conn.cursor()
        cur.execute("SELECT value, created_at FROM cache WHERE key=?", (key,))
        row = cur.fetchone()
        if not row:
            return None
        value, created = row
        if ttl and (time.time() - created) > ttl:
            return None
        try:
            return json.loads(value)
        except Exception:
            return value

    def set(self, key: str, value: Any) -> None:
        cur = self.conn.cursor()
        cur.execute("REPLACE INTO cache (key,value,created_at) VALUES (?,?,?)", (key, json.dumps(value), time.time()))
        self.conn.commit()
