from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import List, Dict


def _rows(conn: sqlite3.Connection, company: str):
    cur = conn.cursor()
    cur.execute('SELECT id,file_path,file_name,last_modified,summary,content FROM documents WHERE company=? AND status=?', (company, 'current'))
    return cur.fetchall()


def search(db_path: str, company: str, query: str, limit: int = 20) -> List[Dict]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = _rows(conn, company)
    if not rows:
        conn.close()
        return []

    tokens = [t.lower() for t in query.strip().split() if t.strip()]
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
        confidence = round(min(1.0, score), 2)
        summary = r['summary'] or ((r['content'] or '')[:300])
        results.append(
            {
                'company': company,
                'file': r['file_name'],
                'path': r['file_path'],
                'last_modified': datetime.utcfromtimestamp(r['last_modified']).isoformat() + 'Z',
                'summary': summary,
                'confidence': confidence,
                'score_raw': score,
            }
        )

    results = sorted(results, key=lambda x: x['score_raw'], reverse=True)[:limit]
    conn.close()
    return results
