"""Market intelligence – detects industry movement signals in news content."""
from __future__ import annotations


_KEY_TERMS = [
    "expansion",
    "investment",
    "new line",
    "capacity",
    "acquisition",
    "plant",
    "price increase",
    "partnership",
    "contract",
]


def build_market_signal(payload: dict) -> dict | None:
    headline = (payload.get("headline") or "").lower()
    summary = (payload.get("summary") or "").lower()
    text = f"{headline} {summary}"
    hits = [term for term in _KEY_TERMS if term in text]
    if not hits:
        return None
    return {
        "impact": "high" if len(hits) >= 2 else "medium",
        "message": "Market movement detected ({}).".format(", ".join(hits[:3])),
        "terms_found": hits,
    }
