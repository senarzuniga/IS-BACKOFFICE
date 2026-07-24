from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict

from backoffice.ui.workbench_framework.scoring import global_score, normalize_scores


def compute_platform_score(kpis_0_10: Dict[str, float]) -> float:
    normalized = normalize_scores(kpis_0_10)
    return global_score(normalized)


def update_platform_score_history(kpis_0_10: Dict[str, float], path: str = "reports/spoe/platform_score_history.jsonl") -> Dict:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    current_score = compute_platform_score(kpis_0_10)
    previous_score = None
    if p.exists():
        lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if lines:
            try:
                previous_score = float(json.loads(lines[-1]).get("global_platform_score"))
            except Exception:
                previous_score = None

    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "kpis_0_10": kpis_0_10,
        "global_platform_score": current_score,
        "previous_global_platform_score": previous_score,
        "delta": None if previous_score is None else round(current_score - previous_score, 2),
    }

    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return payload
