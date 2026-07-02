"""Search helpers for the Competitive Intelligence scaffold.

These functions are thin wrappers around the Indexer and are safe to
call during development. They do not perform network activity.
"""

from __future__ import annotations

from typing import List, Dict, Optional
from pathlib import Path

from .indexer import Indexer


def search(db_path: Optional[Path], company: str, query: str, limit: int = 10) -> List[Dict]:
    idx = Indexer(db_path=db_path)
    return idx.search_by_company_name(company, query, limit=limit)
