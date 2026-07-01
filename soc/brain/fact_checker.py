from __future__ import annotations

from typing import Dict, List


def assess_evidence(evidence: List[Dict]) -> Dict:
    """Perform lightweight fact checking and contradiction detection.

    This is a heuristic implementation intended for prototypes. It
    computes an aggregate confidence and returns any simple
    contradictions detected.
    """
    if not evidence:
        return {'overall_confidence': 0.0, 'contradictions': [], 'notes': 'No evidence provided.'}

    confidences = [float(e.get('confidence', 0.5) or 0.0) for e in evidence]
    overall = sum(confidences) / len(confidences)

    # naive contradiction detection: if two pieces of evidence have
    # identical titles but different snippets, flag possible contradiction
    title_map = {}
    contradictions = []
    for e in evidence:
        t = e.get('title')
        s = e.get('snippet', '')
        if t in title_map and title_map[t] != s:
            contradictions.append({'title': t, 'a': title_map[t][:200], 'b': s[:200]})
        title_map[t] = s

    notes = []
    if not contradictions:
        notes.append('No direct contradictions detected (heuristic).')

    return {'overall_confidence': round(overall, 3), 'contradictions': contradictions, 'notes': notes}
