"""Deterministic cleaning pipeline — orchestrates all cleaning steps."""
from __future__ import annotations
from typing import List, Tuple

from backoffice.ingestion.base import RawRecord
from .normalizer import Normalizer
from .deduplicator import Deduplicator
from .validator import Validator


class CleaningReport:
    def __init__(self):
        self.total_in: int = 0
        self.duplicates_removed: int = 0
        self.validation_errors: List[Tuple[str, List[str]]] = []

    @property
    def total_out(self) -> int:
        return self.total_in - self.duplicates_removed

    def __repr__(self) -> str:
        return (f"CleaningReport(in={self.total_in}, out={self.total_out}, "
                f"dupes_removed={self.duplicates_removed}, "
                f"errors={len(self.validation_errors)})")


class CleaningPipeline:
    """Applies normalization, deduplication, and validation to raw records."""

    def __init__(self):
        self.normalizer = Normalizer()
        self.deduplicator = Deduplicator()
        self.validator = Validator()

    def run(self, records: List[RawRecord]) -> Tuple[List[RawRecord], CleaningReport]:
        report = CleaningReport()
        report.total_in = len(records)

        # 1. Deduplicate by checksum
        deduped = self.deduplicator.deduplicate_raw(records)
        report.duplicates_removed = len(records) - len(deduped)

        # 2. Normalize text content
        cleaned: List[RawRecord] = []
        for rec in deduped:
            if rec.raw_text:
                rec = rec.model_copy(update={"raw_text": self.normalizer.normalize_text(rec.raw_text)})
            cleaned.append(rec)

        # 3. Validate required metadata
        for rec in cleaned:
            ok, errors = self.validator.validate_required(
                rec.model_dump(), ["source_type", "ingested_at"]
            )
            if not ok:
                report.validation_errors.append((rec.record_id, errors))

        return cleaned, report
