from __future__ import annotations

from typing import Dict


def normalize_scores(raw: Dict[str, float], min_value: float = 0.0, max_value: float = 10.0) -> Dict[str, float]:
    span = max(max_value - min_value, 1e-9)
    out: Dict[str, float] = {}
    for k, v in raw.items():
        vv = max(min_value, min(max_value, float(v)))
        out[k] = round(((vv - min_value) / span) * 100.0, 2)
    return out


def global_score(normalized: Dict[str, float], weights: Dict[str, float] | None = None) -> float:
    if not normalized:
        return 0.0
    if not weights:
        return round(sum(normalized.values()) / len(normalized), 2)
    total_w = 0.0
    acc = 0.0
    for k, v in normalized.items():
        w = float(weights.get(k, 1.0))
        total_w += w
        acc += v * w
    if total_w <= 0:
        return round(sum(normalized.values()) / len(normalized), 2)
    return round(acc / total_w, 2)
