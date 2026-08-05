"""Service Proposal Engine — Proposal Number Engine."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from .database import SPEDatabase


class ProposalNumbering:
    """
    Numbering engine for INGECART service proposals.
    Format:  OFF-YYYY-SXXX
    Example: OFF-2026-S131

    The counter is stored in the database (spe_counter table).
    Thread-safe using an in-process lock plus SQLite IMMEDIATE transactions.
    """

    FORMAT = "OFF-{year}-S{num:03d}"

    def __init__(self, db: Optional[SPEDatabase] = None):
        self._db = db or SPEDatabase()

    def next(self, year: Optional[int] = None) -> str:
        """Atomically increment and return the next proposal number."""
        if year is None:
            year = datetime.now().year
        return self._db.next_number(year)

    def preview_next(self) -> str:
        """Return what the next number will be WITHOUT incrementing."""
        year = datetime.now().year
        n = self._db.peek_next_number()
        return self.FORMAT.format(year=year, num=n)

    @staticmethod
    def parse(number: str) -> dict:
        """Parse 'OFF-2026-S131' into {'year':2026, 'seq':131}."""
        try:
            parts = number.split("-")
            if len(parts) == 3 and parts[2].startswith("S"):
                return {"year": int(parts[1]), "seq": int(parts[2][1:])}
        except Exception:
            pass
        return {}
