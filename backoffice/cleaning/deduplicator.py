"""Duplicate detection for raw records and entities."""
from __future__ import annotations
from typing import List, Set, Dict, TypeVar, Sequence

from backoffice.ingestion.base import RawRecord

T = TypeVar("T")


class Deduplicator:
    """Removes duplicate RawRecords and entity objects."""

    def deduplicate_raw(self, records: List[RawRecord]) -> List[RawRecord]:
        """Remove records with identical checksums (keep first)."""
        seen: Set[str] = set()
        result: List[RawRecord] = []
        for rec in records:
            key = rec.checksum or rec.record_id
            if key not in seen:
                seen.add(key)
                result.append(rec)
        return result

    def deduplicate_by_field(self, items: Sequence[Dict], field: str) -> List[Dict]:
        """Remove dicts with duplicate values for a given field."""
        seen: Set = set()
        result = []
        for item in items:
            val = item.get(field)
            if val not in seen:
                seen.add(val)
                result.append(item)
        return result
