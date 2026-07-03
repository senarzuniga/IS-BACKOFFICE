from __future__ import annotations

from typing import List, Dict
from .fact_versioning import FactVersioning
from .contradiction_resolver import ContradictionResolver
from .source_registry import SourceRegistry


class TruthEngine:
    """Coordinate fact ingestion, versioning and contradiction resolution.

    This component accepts extracted fact candidates and applies business
    logic to mark truth status and write versioned records.
    """

    def __init__(self, registry: SourceRegistry, fv: FactVersioning, resolver: ContradictionResolver):
        self.registry = registry
        self.fv = fv
        self.resolver = resolver

    def ingest_facts(self, facts: List[Dict]) -> Dict:
        """Ingest a list of fact dicts and return a resolution summary.

        Expected fact fields: entity, attribute, value, source_id, source_date, confidence
        """
        inserted = []
        for f in facts:
            inserted.append(self.fv.upsert_fact(entity=f['entity'], attribute=f['attribute'], value=str(f['value']), source_id=f['source_id'], source_date=f.get('source_date'), confidence=f.get('confidence', 0.8), meta=f.get('meta')))

        # Resolve per (entity,attribute)
        groups = {}
        for rec in inserted:
            key = (rec.entity, rec.attribute)
            groups.setdefault(key, []).append({
                'value': rec.value,
                'source_id': rec.source_id,
                'source_date': rec.source_date,
                'extraction_ts': rec.extraction_ts,
                'confidence': rec.confidence,
            })

        resolved = {}
        for key, group in groups.items():
            winner, conflicts = self.resolver.resolve_group(group)
            resolved[key] = {'winner': winner, 'conflicts': conflicts}

        return {'inserted': len(inserted), 'resolved': resolved}
