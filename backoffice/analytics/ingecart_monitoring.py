"""Compatibility layer and lightweight monitoring data model for the Smart Plant dashboard.

This module supplies the functions referenced by `pages/smart_plant_dashboard.py`.
It intentionally stays dependency-light so the page can still import even when the
full monitoring stack is not yet wired into the project.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Sequence

ROLE_PANELS: Dict[str, Dict[str, str]] = {
    "Ingecart": {
        "description": "Operación y mantenimiento de sistemas de transporte, paletización y flujo de material.",
        "focus": "Disponibilidad y servicio",
    },
    "Operations": {
        "description": "Supervisión del rendimiento global y del cumplimiento de objetivos de producción.",
        "focus": "OEE y productividad",
    },
    "Maintenance": {
        "description": "Planificación de mantenimiento predictivo y gestión de incidencias críticas.",
        "focus": "Preventivos y piezas de recambio",
    },
    "Commercial": {
        "description": "Alineación de propuestas, negocio de servicio y atención a clientes con necesidad operativa.",
        "focus": "ROI y oportunidades",
    },
}

FORMULA_LIBRARY: List[Dict[str, str]] = [
    {
        "name": "OEE",
        "expression": "Disponibilidad × Rendimiento × Calidad",
        "target": ">= 85%",
    },
    {
        "name": "Disponibilidad",
        "expression": "Tiempo útil / Tiempo planificado",
        "target": ">= 92%",
    },
    {
        "name": "Rendimiento",
        "expression": "Ciclo real / Ciclo ideal",
        "target": ">= 90%",
    },
    {
        "name": "Calidad",
        "expression": "Unidades OK / Unidades totales",
        "target": ">= 98%",
    },
]

SPARE_PART_CATALOG: List[Dict[str, Any]] = [
    {"sku": "IN-TR-224", "name": "Sensor de temperatura", "equipment": "Conveyor 14", "lead_time_days": 3, "stock_level": "Alta"},
    {"sku": "IN-PL-118", "name": "Rodamiento de apoyo", "equipment": "Paletizador", "lead_time_days": 7, "stock_level": "Media"},
    {"sku": "IN-AM-009", "name": "Kit de ruedas AMR", "equipment": "AMR-C", "lead_time_days": 5, "stock_level": "Media"},
    {"sku": "IN-RF-077", "name": "Lector RFID", "equipment": "Handoff", "lead_time_days": 2, "stock_level": "Alta"},
]


def load_monitoring_blueprint() -> Dict[str, Any]:
    """Return a small but realistic blueprint for Smart Plant monitoring."""
    return {
        "name": "INGECART Smart Plant Monitoring",
        "recommended_stack": "Streamlit + Plotly + FastAPI + SQLite",
        "sites": [
            {"id": "site_001", "name": "Planta Norte", "country": "ES", "region": "Europa", "critical_assets": 12},
            {"id": "site_002", "name": "Planta Centro", "country": "FR", "region": "Europa", "critical_assets": 10},
            {"id": "site_003", "name": "Planta Sur", "country": "IT", "region": "Europa", "critical_assets": 11},
        ],
        "scopes": [
            {"id": "all", "label": "Portfolio global"},
            {"id": "site_001", "label": "Planta Norte"},
            {"id": "site_002", "label": "Planta Centro"},
            {"id": "site_003", "label": "Planta Sur"},
        ],
    }


def get_scope_options(blueprint: Dict[str, Any] | None = None) -> List[str]:
    bp = blueprint or load_monitoring_blueprint()
    return ["all"] + [site["id"] for site in bp.get("sites", [])]


def get_scope_label(scope: str, blueprint: Dict[str, Any] | None = None) -> str:
    if scope in (None, "", "all", "all_sites", "portfolio"):
        return "Portfolio global"
    bp = blueprint or load_monitoring_blueprint()
    for site in bp.get("sites", []):
        if site["id"] == scope:
            return site["name"]
    return str(scope)


def _site_names_for_scope(site_scope: str, blueprint: Dict[str, Any]) -> List[Dict[str, Any]]:
    if site_scope in (None, "", "all", "all_sites", "portfolio"):
        return list(blueprint.get("sites", []))
    return [site for site in blueprint.get("sites", []) if site["id"] == site_scope]


def _simulation_series(days: int, interval_minutes: int, site_names: Sequence[str]) -> List[Dict[str, Any]]:
    start = datetime.now(timezone.utc) - timedelta(days=days)
    series: List[Dict[str, Any]] = []
    for index in range(max(1, (days * 24 * 60) // interval_minutes)):
        ts = start + timedelta(minutes=index * interval_minutes)
        base = 80 + ((index % 11) * 1.2)
        for site_index, site_name in enumerate(site_names):
            value = base + site_index * 4.5 + ((index + site_index) % 7) * 0.8
            series.append(
                {
                    "timestamp": ts.isoformat(),
                    "site_name": site_name,
                    "site_id": f"site_{site_index + 1:03d}",
                    "oee_pct": round(max(60.0, min(96.0, value)), 1),
                    "availability_pct": round(max(70.0, min(98.0, value - 2.2)), 1),
                    "energy_mwh": round(5.4 + (index % 6) * 0.6 + site_index * 0.4, 2),
                }
            )
    return series


def generate_monitoring_snapshot(
    site_scope: str = "all",
    role: str = "Ingecart",
    days: int = 7,
    interval_minutes: int = 15,
    blueprint: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    bp = blueprint or load_monitoring_blueprint()
    selected_sites = _site_names_for_scope(site_scope, bp)
    if not selected_sites:
        selected_sites = bp.get("sites", [])

    site_names = [site["name"] for site in selected_sites]
    series = _simulation_series(days=days, interval_minutes=interval_minutes, site_names=site_names)

    site_summaries: List[Dict[str, Any]] = []
    equipment_latest: List[Dict[str, Any]] = []
    for index, site in enumerate(selected_sites):
        base_oee = 86 + (index * 2)
        base_avail = 91 + (index * 1.6)
        base_perf = 88 + (index * 1.3)
        critical_assets = site.get("critical_assets", 8)
        site_summaries.append(
            {
                "site_id": site["id"],
                "site_name": site["name"],
                "oee_pct": base_oee,
                "availability_pct": base_avail,
                "performance_pct": base_perf,
                "quality_pct": 98,
                "critical_assets": critical_assets,
                "pm_due_assets": max(1, critical_assets // 4),
                "annual_recovery_potential_eur": 185000 + index * 55000,
                "summary": "Capacidad estable con margen operativo para mejorar disponibilidad de transporte y paletización.",
                "lpi_pct": 86 + index,
            }
        )
        for asset_index in range(1, min(4, critical_assets // 4) + 1):
            equipment_latest.append(
                {
                    "equipment_id": f"{site['id']}-asset-{asset_index}",
                    "site_id": site["id"],
                    "site_name": site["name"],
                    "equipment_name": f"Equipo {asset_index}",
                    "status": "running" if asset_index % 3 else "warning",
                    "oee_pct": base_oee - 2 + asset_index,
                    "availability_pct": base_avail - 1 + asset_index,
                    "performance_pct": base_perf - 2 + asset_index,
                    "quality_pct": 98,
                    "alert_count": 1 if asset_index % 2 else 0,
                    "last_seen_minutes_ago": 7 + asset_index,
                }
            )

    portfolio = {
        "oee_pct": round(sum(item["oee_pct"] for item in site_summaries) / max(len(site_summaries), 1), 1),
        "availability_pct": round(sum(item["availability_pct"] for item in site_summaries) / max(len(site_summaries), 1), 1),
        "performance_pct": round(sum(item["performance_pct"] for item in site_summaries) / max(len(site_summaries), 1), 1),
        "active_alerts": sum(1 for item in equipment_latest if item["status"] == "warning"),
        "energy_mwh_week": 185.0,
        "annual_recovery_potential_eur": round(sum(item["annual_recovery_potential_eur"] for item in site_summaries), 2),
        "service_opportunity_eur": 820000.0,
    }

    alerts = [
        {
            "id": "AL-1001",
            "site_id": selected_sites[0]["id"] if selected_sites else "site_001",
            "equipment_id": (equipment_latest[0]["equipment_id"] if equipment_latest else "asset-01"),
            "severity": "medium",
            "message": "Evolución térmica por encima del rango en el transporte principal.",
            "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=35)).isoformat(),
        }
    ]

    interventions = [
        {
            "job_id": "PM-203",
            "site_id": selected_sites[0]["id"] if selected_sites else "site_001",
            "equipment_id": (equipment_latest[0]["equipment_id"] if equipment_latest else "asset-01"),
            "type": "Mantenimiento predictivo",
            "status": "programado",
        }
    ]

    recommendations = [
        {
            "title": "Rebalancear flujo de AMR",
            "impact_eur": 76000.0,
            "priority": "alta",
            "reason": "El traspaso entre líneas se encuentra saturado al 78% de capacidad.",
        },
        {
            "title": "Estabilizar stock de repuestos críticos",
            "impact_eur": 34000.0,
            "priority": "media",
            "reason": "Los sensores de temperatura y lectores RFID tienen tiempos de entrega bajos.",
        },
    ]

    return {
        "scope": site_scope,
        "scope_label": get_scope_label(site_scope, bp),
        "role": role,
        "blueprint": bp,
        "portfolio": portfolio,
        "site_summaries": site_summaries,
        "equipment_latest": equipment_latest,
        "series": series,
        "alerts": alerts,
        "interventions": interventions,
        "recommendations": recommendations,
        "simulation_assumptions": {
            "shift_count": 3,
            "interval_minutes": interval_minutes,
            "days": days,
            "forecast_window_days": 14,
        },
    }


def generate_instant_offer(
    site_scope: str = "all",
    role: str = "Ingecart",
    equipment: Iterable[str] | None = None,
    blueprint: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    bp = blueprint or load_monitoring_blueprint()
    scope_label = get_scope_label(site_scope, bp)
    assets = list(equipment or ["conveyor", "amr", "paletizer"])
    offer = {
        "title": f"Oferta instantánea para {scope_label}",
        "scope": site_scope,
        "role": role,
        "assets": assets,
        "estimated_roi_pct": 24,
        "annual_savings_eur": 182000.0,
        "payback_months": 9,
        "recommended_actions": [
            "Revisión de flujo y sincronización de AMRs",
            "Recalibración de sensores en el transporte principal",
            "Ajuste de la estrategia de mantenimiento predictivo",
        ],
        "confidence": 0.87,
    }
    return offer


def suggest_spare_parts(
    site_scope: str = "all",
    equipment_ids: Sequence[str] | None = None,
    blueprint: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    _ = blueprint, site_scope
    selected = list(SPARE_PART_CATALOG)
    if equipment_ids:
        relevant = []
        for item in selected:
            if any(eq in item["equipment"].lower() for eq in [k.lower() for k in equipment_ids]):
                relevant.append(item)
        if relevant:
            selected = relevant
    return selected


def build_request_alert(
    customer_name: str = "Cliente",
    request_type: str = "solicitud",
    urgency: str = "media",
    details: str = "",
) -> Dict[str, Any]:
    return {
        "customer_name": customer_name,
        "request_type": request_type,
        "urgency": urgency,
        "details": details or "Necesidad de revisión de capacidad y optimización de flujo operativo.",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


__all__ = [
    "ROLE_PANELS",
    "FORMULA_LIBRARY",
    "SPARE_PART_CATALOG",
    "load_monitoring_blueprint",
    "generate_monitoring_snapshot",
    "generate_instant_offer",
    "suggest_spare_parts",
    "build_request_alert",
    "get_scope_label",
    "get_scope_options",
]
