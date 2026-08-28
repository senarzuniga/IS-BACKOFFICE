"""FastAPI routes for the Ingecart Industrial Monitoring Copilot.

Endpoints:
  GET  /ingecart-monitoring/blueprint        - Equipment blueprint (5 plants, 18 assets)
  POST /ingecart-monitoring/snapshot         - Monitoring snapshot (signals + KPIs, no time-series)
  POST /ingecart-monitoring/snapshot/full    - Snapshot with full time-series signal array
  POST /ingecart-monitoring/offer            - Instant service/contract offer
  GET  /ingecart-monitoring/roles            - Roles and their focus metrics/documents
  GET  /ingecart-monitoring/formulas         - KPI formula library
  GET  /ingecart-monitoring/scopes           - Valid scope values with labels
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backoffice.analytics.ingecart_monitoring import (
    FORMULA_LIBRARY,
    ROLE_PANELS,
    generate_instant_offer,
    generate_monitoring_snapshot,
    get_scope_label,
    get_scope_options,
    load_monitoring_blueprint,
)

router = APIRouter(prefix="/ingecart-monitoring", tags=["Ingecart Monitoring"])

_VALID_OFFER_KINDS = {"maintenance_contract", "materials_and_spares", "improvement_upgrade", "corrective_intervention"}
_VALID_COVERAGES = {"business_hours", "extended", "24x7"}
_VALID_URGENCIES = {"standard", "priority", "emergency"}


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class SnapshotRequest(BaseModel):
    site_scope: str = Field("all", description="'all' or a site ID ('1'..'5')")
    role: str = Field("Ingecart", description="Role: Operario, Mantenimiento, Jefe de planta, Gerencia, Ingecart")
    days: int = Field(7, ge=1, le=30, description="Historical horizon in days")
    interval_minutes: int = Field(15, description="Signal resolution: 15, 30, or 60 minutes")


class OfferRequest(BaseModel):
    site_scope: str = Field("all", description="'all' or a site ID ('1'..'5')")
    offer_kind: str = Field(
        "maintenance_contract",
        description="maintenance_contract | materials_and_spares | improvement_upgrade | corrective_intervention",
    )
    target_equipment_id: str = Field("all", description="Specific equipment ID or 'all'")
    coverage: str = Field("24x7", description="business_hours | extended | 24x7")
    urgency: str = Field("priority", description="standard | priority | emergency")


# ---------------------------------------------------------------------------
# Internal validators
# ---------------------------------------------------------------------------


def _validate_scope(site_scope: str, blueprint: Dict[str, Any]) -> None:
    valid = get_scope_options(blueprint)
    if site_scope not in valid:
        raise HTTPException(status_code=422, detail=f"Invalid site_scope '{site_scope}'. Valid: {valid}")


def _validate_role(role: str) -> None:
    if role not in ROLE_PANELS:
        raise HTTPException(status_code=422, detail=f"Invalid role '{role}'. Valid: {list(ROLE_PANELS.keys())}")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/blueprint", summary="Equipment blueprint for all 5 plants")
def get_blueprint() -> Dict[str, Any]:
    """Full monitoring blueprint: sites, equipment families, shift model."""
    blueprint = load_monitoring_blueprint()
    return {
        "company_code": blueprint["company_code"],
        "company_name": blueprint["company_name"],
        "sector": blueprint["sector"],
        "shift_model": blueprint["shift_model"],
        "site_count": len(blueprint["sites"]),
        "sites": [
            {
                "id": site["id"],
                "name": site["name"],
                "country": site["country"],
                "summary": site["summary"],
                "equipment_count": len(site["equipment"]),
                "equipment": [
                    {
                        "id": eq["id"],
                        "name": eq["name"],
                        "family_group": eq["family_group"],
                        "nominal_throughput_per_hour": eq["nominal_throughput_per_hour"],
                        "pm_cycle_hours": eq["pm_cycle_hours"],
                        "mtbf_hours": eq["mtbf_hours"],
                    }
                    for eq in site["equipment"]
                ],
            }
            for site in blueprint["sites"]
        ],
    }


@router.post("/snapshot", summary="Generate live monitoring snapshot (KPIs, alerts, recommendations)")
def post_snapshot(request: SnapshotRequest) -> Dict[str, Any]:
    """Deterministic snapshot for the last N days.
    Returns: KPIs, alerts, recommendations, interventions, contracts.
    Time-series excluded. Use /snapshot/full for raw signals."""
    blueprint = load_monitoring_blueprint()
    _validate_scope(request.site_scope, blueprint)
    _validate_role(request.role)
    if request.interval_minutes not in (15, 30, 60):
        raise HTTPException(status_code=422, detail="interval_minutes must be 15, 30, or 60.")
    snapshot = generate_monitoring_snapshot(
        site_scope=request.site_scope,
        role=request.role,
        days=request.days,
        interval_minutes=request.interval_minutes,
        blueprint=blueprint,
    )
    result = {k: v for k, v in snapshot.items() if k not in ("series", "blueprint")}
    result["series_count"] = len(snapshot.get("series", []))
    return result


@router.post("/snapshot/full", summary="Snapshot with complete time-series signal array")
def post_snapshot_full(request: SnapshotRequest) -> Dict[str, Any]:
    """Same as /snapshot but includes all raw signal rows. Use for charting or CSV export."""
    blueprint = load_monitoring_blueprint()
    _validate_scope(request.site_scope, blueprint)
    _validate_role(request.role)
    if request.interval_minutes not in (15, 30, 60):
        raise HTTPException(status_code=422, detail="interval_minutes must be 15, 30, or 60.")
    return generate_monitoring_snapshot(
        site_scope=request.site_scope,
        role=request.role,
        days=request.days,
        interval_minutes=request.interval_minutes,
        blueprint=blueprint,
    )


@router.post("/offer", summary="Generate an instant service/contract offer")
def post_offer(request: OfferRequest) -> Dict[str, Any]:
    """Generate an instant offer driven by live monitoring signals.
    Builds a 3-day Ingecart-role snapshot internally, then runs the offer engine."""
    blueprint = load_monitoring_blueprint()
    _validate_scope(request.site_scope, blueprint)
    if request.offer_kind not in _VALID_OFFER_KINDS:
        raise HTTPException(status_code=422, detail=f"Invalid offer_kind. Valid: {sorted(_VALID_OFFER_KINDS)}")
    if request.coverage not in _VALID_COVERAGES:
        raise HTTPException(status_code=422, detail=f"Invalid coverage. Valid: {sorted(_VALID_COVERAGES)}")
    if request.urgency not in _VALID_URGENCIES:
        raise HTTPException(status_code=422, detail=f"Invalid urgency. Valid: {sorted(_VALID_URGENCIES)}")
    snapshot = generate_monitoring_snapshot(
        site_scope=request.site_scope,
        role="Ingecart",
        days=3,
        interval_minutes=60,
        blueprint=blueprint,
    )
    return generate_instant_offer(
        snapshot=snapshot,
        request_kind=request.offer_kind,
        target_equipment_id=request.target_equipment_id,
        coverage=request.coverage,
        urgency=request.urgency,
    )


@router.get("/roles", summary="List monitoring roles and their panel definitions")
def get_roles() -> Dict[str, Any]:
    """Role names, descriptions, focus metrics and document types."""
    return {
        role: {
            "description": panel["description"],
            "focus_metrics": panel["focus_metrics"],
            "documents": panel["documents"],
        }
        for role, panel in ROLE_PANELS.items()
    }


@router.get("/formulas", summary="KPI formula library")
def get_formulas() -> List[Dict[str, str]]:
    """OEE, LPI, PM compliance, intervention priority, service opportunity formulas."""
    return FORMULA_LIBRARY


@router.get("/scopes", summary="Available scope values with human-readable labels")
def get_scopes() -> Dict[str, Any]:
    """Valid site_scope values: 'all' and individual site IDs 1-5."""
    blueprint = load_monitoring_blueprint()
    options = get_scope_options(blueprint)
    return {
        "scopes": [
            {"value": value, "label": get_scope_label(value, blueprint)}
            for value in options
        ]
    }
