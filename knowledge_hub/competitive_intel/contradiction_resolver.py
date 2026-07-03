from __future__ import annotations

from typing import List, Dict, Tuple
from .source_registry import SourceRegistry


class ContradictionResolver:
    """Resolve conflicting facts using simple heuristics.

    Heuristics (initial): prefer higher `trust` value from SourceRegistry.
    If tie, prefer the most recent `source_date` / extraction timestamp.
    """

    def __init__(self, registry: SourceRegistry):
        self.registry = registry

    def resolve_group(self, fact_group: List[Dict]) -> Tuple[Dict, List[Dict]]:
        """Given a group of fact dicts (same entity+attribute) return (winner, conflicts).

        Fact dicts are expected to include: `value`, `source_id`, `source_date`, `extraction_ts`.
        """
        if not fact_group:
            return {}, []

        # Map source -> trust
        scored = []
        for f in fact_group:
            s = self.registry.get(f.get('source_id')) or {}
            trust = int(s.get('trust', 3)) if s else 3
            ts = f.get('source_date') or f.get('extraction_ts') or 0
            scored.append((trust, ts, f))

        # Sort by trust desc then timestamp desc
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        winner = scored[0][2]
        conflicts = [x[2] for x in scored[1:]]
        return winner, conflicts
