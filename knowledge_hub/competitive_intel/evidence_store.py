from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Iterator, List
from pathlib import Path
import json
import uuid
import time


@dataclass
class Evidence:
    id: str
    source_id: str
    doc_id: Optional[str]
    text: str
    source_date: Optional[float]
    extraction_ts: float
    confidence: float
    meta: Dict = field(default_factory=dict)


class EvidenceStore:
    """Lightweight JSONL evidence ledger. Append-only store of extracted evidence.

    Each line in `evidence.jsonl` is a JSON object with provenance metadata.
    """

    def __init__(self, storage_dir: Optional[Path] = None) -> None:
        self.base = Path(storage_dir) if storage_dir else Path(__file__).parent / 'data'
        self.base.mkdir(parents=True, exist_ok=True)
        self.file = self.base / 'evidence.jsonl'
        if not self.file.exists():
            self.file.write_text('', encoding='utf-8')

    def add_evidence(self, source_id: str, doc_id: Optional[str], text: str, source_date: Optional[float] = None, confidence: float = 0.8, meta: Optional[Dict] = None) -> Evidence:
        ev = Evidence(id=uuid.uuid4().hex, source_id=source_id, doc_id=doc_id, text=text, source_date=source_date, extraction_ts=time.time(), confidence=float(confidence), meta=meta or {})
        with self.file.open('a', encoding='utf-8') as fh:
            fh.write(json.dumps(asdict(ev), ensure_ascii=False) + "\n")
        return ev

    def iter_evidence(self) -> Iterator[Evidence]:
        with self.file.open('r', encoding='utf-8') as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    o = json.loads(line)
                    yield Evidence(**o)
                except Exception:
                    continue

    def query_by_source(self, source_id: str) -> List[Evidence]:
        return [e for e in self.iter_evidence() if e.source_id == source_id]

    def query_recent(self, limit: int = 50) -> List[Evidence]:
        items = sorted(list(self.iter_evidence()), key=lambda e: e.extraction_ts, reverse=True)
        return items[:limit]
