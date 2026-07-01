from __future__ import annotations

from typing import Dict, List


def collect_evidence(memory_results: List[Dict], local_results: List[Dict], top_k: int = 6) -> List[Dict]:
    """Merge and deduplicate evidence from memory and local search results.

    Returns a ranked list of evidence items containing minimal metadata
    (doc_uuid, title, snippet, source_ref, last_modified, confidence).
    """
    seen = set()
    merged: List[Dict] = []

    for src in (memory_results or []) + (local_results or []):
        doc_uuid = src.get('uuid') or src.get('doc_uuid') or src.get('id')
        if doc_uuid in seen:
            continue
        seen.add(doc_uuid)
        item = {
            'doc_uuid': doc_uuid,
            'title': src.get('file') or src.get('file_name') or 'document',
            'snippet': (src.get('summary') or '')[:800],
            'source_ref': src.get('source_ref') or src.get('path') or None,
            'last_modified': src.get('last_modified'),
            'confidence': src.get('confidence', 0.5),
        }
        merged.append(item)

    # rank by confidence then recency
    merged = sorted(merged, key=lambda x: ((x.get('confidence') or 0), x.get('last_modified') or 0), reverse=True)
    return merged[:top_k]
