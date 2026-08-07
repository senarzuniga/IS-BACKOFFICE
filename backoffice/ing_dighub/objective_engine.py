from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DomainPressure:
    kam: float
    offers: float
    actions: float


DEFAULT_OBJECTIVE_WEIGHTS: dict[str, float] = {
    "mission_score": 0.34,
    "hypothesis_score": 0.22,
    "mission_health": 0.20,
    "blended_return": 0.24,
    "pressure_kam": 0.12,
    "pressure_offers": 0.12,
    "pressure_actions": 0.12,
}

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "ing_dighub_objective_weights.json"


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp_100(value: float) -> float:
    return max(0.0, min(100.0, value))


def _normalized_base_weights(raw: dict[str, float]) -> dict[str, float]:
    keys = ["mission_score", "hypothesis_score", "mission_health", "blended_return"]
    vals = {k: max(0.0, _to_float(raw.get(k), DEFAULT_OBJECTIVE_WEIGHTS[k])) for k in keys}
    total = sum(vals.values())
    if total <= 0:
        return {k: DEFAULT_OBJECTIVE_WEIGHTS[k] for k in keys}
    return {k: vals[k] / total for k in keys}


def load_objective_weights() -> dict[str, float]:
    loaded = dict(DEFAULT_OBJECTIVE_WEIGHTS)
    if _CONFIG_PATH.exists():
        try:
            payload = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                for key in loaded:
                    if key in payload:
                        loaded[key] = max(0.0, _to_float(payload.get(key), loaded[key]))
        except Exception:
            pass

    base = _normalized_base_weights(loaded)
    return {
        "mission_score": round(base["mission_score"], 4),
        "hypothesis_score": round(base["hypothesis_score"], 4),
        "mission_health": round(base["mission_health"], 4),
        "blended_return": round(base["blended_return"], 4),
        "pressure_kam": round(loaded["pressure_kam"], 4),
        "pressure_offers": round(loaded["pressure_offers"], 4),
        "pressure_actions": round(loaded["pressure_actions"], 4),
    }


def _pressure_from_snapshot(snapshot: dict[str, Any]) -> DomainPressure:
    offers = snapshot.get("offers", {})
    actions = snapshot.get("actions", {})
    kam = snapshot.get("kam", {})

    acceptance = _to_float(offers.get("accepted_ratio_pct"), 0.0)
    open_actions = _to_float(actions.get("open_actions"), 0.0)
    unresolved_actions = _to_float(actions.get("unresolved_ratio_pct"), 0.0)
    avg_health = _to_float(kam.get("avg_account_health"), 0.0)

    offers_pressure = _clamp_100(100.0 - acceptance)
    actions_pressure = _clamp_100((open_actions * 2.0) + unresolved_actions)
    kam_pressure = _clamp_100(100.0 - avg_health)

    return DomainPressure(kam=kam_pressure, offers=offers_pressure, actions=actions_pressure)


def _mission_domain_fit(mission_name: str) -> tuple[float, float, float]:
    low = (mission_name or "").lower()
    kam_fit = 0.5
    offers_fit = 0.5
    actions_fit = 0.5

    if "spoe" in low or "offer" in low or "proposal" in low:
        offers_fit = 1.0
    if "capability" in low or "account" in low or "customer" in low:
        kam_fit = 1.0
    if "mission" in low or "governance" in low or "sync" in low:
        actions_fit = 0.8

    return kam_fit, offers_fit, actions_fit


def rank_missions(missions: list[dict[str, Any]], domain_snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    pressure = _pressure_from_snapshot(domain_snapshot)
    weights = load_objective_weights()
    ranked: list[dict[str, Any]] = []

    for mission in missions:
        mission_health = _to_float(mission.get("mission_health"), 0.0)
        mission_score = _to_float(mission.get("mission_score"), 0.0)
        hypothesis_score = _to_float(mission.get("hypothesis_score"), mission_score)

        engineering_return = _to_float(mission.get("engineering_return"), 0.0) * 10.0
        business_return = _to_float(mission.get("business_return"), 0.0) * 10.0
        knowledge_return = _to_float(mission.get("knowledge_return"), 0.0) * 10.0
        blended_return = (engineering_return + business_return + knowledge_return) / 3.0

        kam_fit, offers_fit, actions_fit = _mission_domain_fit(str(mission.get("name", "")))
        pressure_bonus = (
            pressure.kam * kam_fit * weights["pressure_kam"]
            + pressure.offers * offers_fit * weights["pressure_offers"]
            + pressure.actions * actions_fit * weights["pressure_actions"]
        )

        status = str(mission.get("status", "")).lower()
        status_multiplier = 1.0
        if status == "queued":
            status_multiplier = 1.08
        elif status == "running":
            status_multiplier = 1.03
        elif status == "completed":
            status_multiplier = 0.92

        base_score = (
            mission_score * weights["mission_score"]
            + hypothesis_score * weights["hypothesis_score"]
            + mission_health * weights["mission_health"]
            + blended_return * weights["blended_return"]
        )
        final_score = _clamp_100((base_score + pressure_bonus) * status_multiplier)

        row = dict(mission)
        row["objective_score"] = round(final_score, 2)
        row["pressure_kam"] = round(pressure.kam, 2)
        row["pressure_offers"] = round(pressure.offers, 2)
        row["pressure_actions"] = round(pressure.actions, 2)
        row["weights_version"] = "config-v1"
        ranked.append(row)

    ranked.sort(key=lambda r: r.get("objective_score", 0.0), reverse=True)
    return ranked
