from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict
from pathlib import Path
import json
import uuid
import time


@dataclass
class Source:
    id: str
    name: str
    url: str
    company: str
    trust: int = 3
    type: str = 'web'
    frequency: Optional[str] = None
    ingestion_status: str = 'pending'
    extractor: Optional[str] = None
    meta: Dict = field(default_factory=dict)


class SourceRegistry:
    """Simple file-backed registry for ingestion sources.

    Storage format: JSON array of source objects in `data/sources.json`.
    This is intentionally simple and replaceable by a DB-backed registry later.
    """

    def __init__(self, storage_dir: Optional[Path] = None) -> None:
        self.base = Path(storage_dir) if storage_dir else Path(__file__).parent / 'data'
        self.base.mkdir(parents=True, exist_ok=True)
        self.file = self.base / 'sources.json'
        self._load()

    def _load(self) -> None:
        if self.file.exists():
            try:
                self._items = json.loads(self.file.read_text(encoding='utf-8'))
            except Exception:
                self._items = []
        else:
            self._items = []

    def _save(self) -> None:
        self.file.write_text(json.dumps(self._items, indent=2), encoding='utf-8')

    def register_source(self, name: str, url: str, company: str, **kwargs) -> Source:
        sid = uuid.uuid4().hex
        src = Source(id=sid, name=name, url=url, company=company, **kwargs)
        self._items.append(asdict(src))
        self._save()
        return src

    def list_sources(self, company: Optional[str] = None) -> List[Dict]:
        if company:
            return [s for s in self._items if s.get('company') == company]
        return list(self._items)

    def get(self, source_id: str) -> Optional[Dict]:
        for s in self._items:
            if s.get('id') == source_id:
                return s
        return None

    def update_status(self, source_id: str, status: str) -> bool:
        for s in self._items:
            if s.get('id') == source_id:
                s['ingestion_status'] = status
                s['meta'] = s.get('meta', {})
                s['meta']['last_status_update'] = time.time()
                self._save()
                return True
        return False
