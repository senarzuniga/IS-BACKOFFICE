from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, List
from pathlib import Path
import json
import uuid
import time


@dataclass
class FactRecord:
    id: str
    entity: str
    attribute: str
    value: str
    source_id: str
    source_date: Optional[float]
    extraction_ts: float
    confidence: float
    truth_status: str = 'insufficient_evidence'
    meta: Dict = field(default_factory=dict)


class FactVersioning:
    """Append-only fact versioning store (JSONL).

    Each call to `upsert_fact` records a new version. Consumers query history
    and compute the current candidate fact using business logic.
    """

    def __init__(self, storage_dir: Optional[Path] = None) -> None:
        self.base = Path(storage_dir) if storage_dir else Path(__file__).parent / 'data'
        self.base.mkdir(parents=True, exist_ok=True)
        self.file = self.base / 'facts.jsonl'
        if not self.file.exists():
            self.file.write_text('', encoding='utf-8')

    def upsert_fact(self, entity: str, attribute: str, value: str, source_id: str, source_date: Optional[float] = None, confidence: float = 0.8, meta: Optional[Dict] = None) -> FactRecord:
        fr = FactRecord(id=uuid.uuid4().hex, entity=entity, attribute=attribute, value=value, source_id=source_id, source_date=source_date, extraction_ts=time.time(), confidence=float(confidence), truth_status='insufficient_evidence', meta=meta or {})
        with self.file.open('a', encoding='utf-8') as fh:
            fh.write(json.dumps(asdict(fr), ensure_ascii=False) + '\n')
        return fr

    def history(self, entity: str, attribute: str) -> List[FactRecord]:
        items: List[FactRecord] = []
        with self.file.open('r', encoding='utf-8') as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    o = json.loads(line)
                    if o.get('entity') == entity and o.get('attribute') == attribute:
                        items.append(FactRecord(**o))
                except Exception:
                    continue
        return sorted(items, key=lambda x: x.extraction_ts)

    def current(self, entity: str, attribute: str) -> Optional[FactRecord]:
        hs = self.history(entity, attribute)
        return hs[-1] if hs else None
