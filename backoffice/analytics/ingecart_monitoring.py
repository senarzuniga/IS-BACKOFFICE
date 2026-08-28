"""Deterministic Ingecart monitoring simulator and dashboard data builder."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta
import hashlib
import math
import random
from typing import Any, Dict, Iterable, List


ROLE_PANELS: Dict[str, Dict[str, Any]] = {
    "Operario": {
        "description": "Seguimiento de estado, alarmas, ritmo y ayudas operativas por turno.",
        "focus_metrics": ["state", "throughput_per_hour", "alarm_count", "queue_pct", "quality_pct"],
        "documents": ["Parte de turno", "Solicitud de intervención", "Checklist de arranque"],
    },
    "Mantenimiento": {
        "description": "Salud del activo, riesgo, backlog preventivo, repuestos y MTTR/MTBF.",
        "focus_metrics": ["predicted_failure_risk_pct", "health_score", "maintenance_due_days", "temperature_c", "vibration_mm_s"],
        "documents": ["OT preventiva", "OT correctiva", "Lista de repuestos críticos"],
    },
    "Jefe de planta": {
        "description": "OEE, pérdidas, cuellos de botella, comparativa por turno y por planta.",
        "focus_metrics": ["oee_pct", "availability_pct", "performance_pct", "quality_pct", "lpi_pct"],
        "documents": ["Informe diario", "Resumen de pérdidas", "Plan de acciones"],
    },
    "Gerencia": {
        "description": "Visión multi-planta, coste de paradas, riesgo de servicio y oportunidades de mejora.",
        "focus_metrics": ["oee_pct", "energy_mwh_week", "annual_recovery_potential_eur", "critical_assets", "active_alerts"],
        "documents": ["Executive review", "Pipeline de ahorro", "Riesgos y CAPEX/OPEX"],
    },
    "Ingecart": {
        "description": "Acceso total a operación, mantenimiento, benchmarking y problemas latentes no reportados.",
        "focus_metrics": ["oee_pct", "predicted_failure_risk_pct", "annual_recovery_potential_eur", "hidden_issue_count", "service_opportunity_eur"],
        "documents": ["Informe cliente", "Oferta inmediata", "Plan de contrato", "Benchmark multi-planta"],
    },
}

FORMULA_LIBRARY: List[Dict[str, str]] = [
    {
        "metric": "OEE",
        "formula": "Availability x Performance x Quality",
        "signals": "availability_pct, performance_pct, quality_pct",
        "use_case": "Eficiencia global por equipo, planta o portfolio.",
    },
    {
        "metric": "LPI",
        "formula": "0.45 x queue_pct + 0.30 x alarm_density + 0.25 x predicted_failure_risk_pct",
        "signals": "queue_pct, alarm_count, predicted_failure_risk_pct",
        "use_case": "Presión logística y riesgo de bloqueo aguas abajo.",
    },
    {
        "metric": "PM compliance",
        "formula": "100 x max(0, 1 - overdue_runtime_h / pm_cycle_h)",
        "signals": "runtime_since_pm_h, pm_cycle_h",
        "use_case": "Cumplimiento de mantenimiento preventivo.",
    },
    {
        "metric": "Intervention priority",
        "formula": "0.5 x predicted_failure_risk_pct + 0.3 x downtime_cost_factor + 0.2 x alarm_severity",
        "signals": "predicted_failure_risk_pct, cost_of_downtime_eur_h, alarm_count",
        "use_case": "Priorizar OT, desplazamientos y SLA.",
    },
    {
        "metric": "Service opportunity",
        "formula": "(100 - oee_pct) x cost_of_downtime_eur_h x recoverable_share",
        "signals": "oee_pct, cost_of_downtime_eur_h",
        "use_case": "Generar negocio desde el dolor real del cliente.",
    },
]

DEFAULT_BLUEPRINT: Dict[str, Any] = {
    "company_code": "ingecart-monitoring",
    "company_name": "Ingecart Industrial Monitoring",
    "sector": "Corrugated automation, intralogistics and industrial digital twin",
    "recommended_stack": "Streamlit + Plotly + deterministic digital-twin signals + AI copilot recommendations",
    "holiday_weekday": 6,
    "shift_model": [
        {"name": "Turno 1", "start_hour": 6, "end_hour": 14, "performance_factor": 1.00},
        {"name": "Turno 2", "start_hour": 14, "end_hour": 22, "performance_factor": 1.03},
        {"name": "Turno 3", "start_hour": 22, "end_hour": 6, "performance_factor": 0.94},
    ],
    "sites": [
        {
            "id": "1",
            "name": "Cartonajes Font",
            "country": "Spain",
            "summary": "Línea final con paletización, transporte interno y carga automática de expediciones.",
            "equipment": [
                {
                    "id": "site1_hdp_01",
                    "name": "Heavy Duty Palletizer",
                    "family_group": "palletizer",
                    "nominal_throughput_per_hour": 68,
                    "nominal_cycle_seconds": 53,
                    "energy_kw": 48,
                    "temperature_base_c": 41,
                    "vibration_base_mm_s": 2.4,
                    "mtbf_hours": 156,
                    "mttr_hours": 1.8,
                    "pm_cycle_hours": 168,
                    "cost_of_downtime_eur_h": 1700,
                    "replacement_value_eur": 235000,
                    "recommended_spares_eur": 10500,
                    "monthly_contract_eur": 1450,
                    "service_levers": ["patrones", "interlayers", "visión artificial", "trazabilidad palet"],
                },
                {
                    "id": "site1_ppp_01",
                    "name": "Plug and Play Palletizer",
                    "family_group": "palletizer",
                    "nominal_throughput_per_hour": 54,
                    "nominal_cycle_seconds": 61,
                    "energy_kw": 34,
                    "temperature_base_c": 39,
                    "vibration_base_mm_s": 2.1,
                    "mtbf_hours": 148,
                    "mttr_hours": 1.6,
                    "pm_cycle_hours": 160,
                    "cost_of_downtime_eur_h": 1420,
                    "replacement_value_eur": 165000,
                    "recommended_spares_eur": 8200,
                    "monthly_contract_eur": 1180,
                    "service_levers": ["recipe tuning", "bundle stability", "remote support"],
                },
                {
                    "id": "site1_conv_01",
                    "name": "Belt Conveyors + Transfercar",
                    "family_group": "conveyor",
                    "nominal_throughput_per_hour": 132,
                    "nominal_cycle_seconds": 19,
                    "energy_kw": 26,
                    "temperature_base_c": 34,
                    "vibration_base_mm_s": 1.7,
                    "mtbf_hours": 210,
                    "mttr_hours": 1.1,
                    "pm_cycle_hours": 180,
                    "cost_of_downtime_eur_h": 1180,
                    "replacement_value_eur": 145000,
                    "recommended_spares_eur": 6900,
                    "monthly_contract_eur": 840,
                    "service_levers": ["handoff logic", "accumulation control", "jam analytics"],
                },
                {
                    "id": "site1_ship_01",
                    "name": "Truck Autoloading System",
                    "family_group": "truck_loader",
                    "nominal_throughput_per_hour": 22,
                    "nominal_cycle_seconds": 163,
                    "energy_kw": 29,
                    "temperature_base_c": 36,
                    "vibration_base_mm_s": 1.9,
                    "mtbf_hours": 194,
                    "mttr_hours": 1.3,
                    "pm_cycle_hours": 180,
                    "cost_of_downtime_eur_h": 1350,
                    "replacement_value_eur": 180000,
                    "recommended_spares_eur": 7600,
                    "monthly_contract_eur": 960,
                    "service_levers": ["dock scheduling", "expedition ETA", "auto-sequencing"],
                },
            ],
        },
        {
            "id": "2",
            "name": "Cascades Sonoco-Calgary",
            "country": "Canada",
            "summary": "Transfercar para salidas RDC, conveyors de FG/cosedora y lógica BHS/Ingecart para bottom/tie sheets.",
            "equipment": [
                {
                    "id": "site2_transfer_01",
                    "name": "Transfercar + 3 RDC Outfeed Belt Conveyors",
                    "family_group": "conveyor",
                    "nominal_throughput_per_hour": 148,
                    "nominal_cycle_seconds": 17,
                    "energy_kw": 31,
                    "temperature_base_c": 35,
                    "vibration_base_mm_s": 1.8,
                    "mtbf_hours": 198,
                    "mttr_hours": 1.2,
                    "pm_cycle_hours": 172,
                    "cost_of_downtime_eur_h": 1600,
                    "replacement_value_eur": 210000,
                    "recommended_spares_eur": 9400,
                    "monthly_contract_eur": 1280,
                    "service_levers": ["dynamic routing", "priority rules", "RDC evacuation"],
                },
                {
                    "id": "site2_fg_01",
                    "name": "2 Belt Conveyors FG + Stitcher Infeed",
                    "family_group": "conveyor",
                    "nominal_throughput_per_hour": 121,
                    "nominal_cycle_seconds": 21,
                    "energy_kw": 22,
                    "temperature_base_c": 33,
                    "vibration_base_mm_s": 1.5,
                    "mtbf_hours": 205,
                    "mttr_hours": 0.9,
                    "pm_cycle_hours": 176,
                    "cost_of_downtime_eur_h": 1220,
                    "replacement_value_eur": 120000,
                    "recommended_spares_eur": 5400,
                    "monthly_contract_eur": 760,
                    "service_levers": ["FG buffering", "stitcher feed stability", "anti-jam tuning"],
                },
                {
                    "id": "site2_bhs_01",
                    "name": "Bottom/Tie Sheets BHS-Ingecart Handoff",
                    "family_group": "sheet_handoff",
                    "nominal_throughput_per_hour": 46,
                    "nominal_cycle_seconds": 77,
                    "energy_kw": 19,
                    "temperature_base_c": 31,
                    "vibration_base_mm_s": 1.4,
                    "mtbf_hours": 184,
                    "mttr_hours": 1.0,
                    "pm_cycle_hours": 168,
                    "cost_of_downtime_eur_h": 980,
                    "replacement_value_eur": 90000,
                    "recommended_spares_eur": 4200,
                    "monthly_contract_eur": 640,
                    "service_levers": ["Kuka pallet availability", "touchpad call logic", "WIP reservation"],
                },
            ],
        },
        {
            "id": "3",
            "name": "Cascades Sonoco-Waterloo",
            "country": "Canada",
            "summary": "Dos heavy duty palletizer en la salida de una Mitsubishi Evol.",
            "equipment": [
                {
                    "id": "site3_hdp_01",
                    "name": "Heavy Duty Palletizer A",
                    "family_group": "palletizer",
                    "nominal_throughput_per_hour": 70,
                    "nominal_cycle_seconds": 51,
                    "energy_kw": 47,
                    "temperature_base_c": 40,
                    "vibration_base_mm_s": 2.3,
                    "mtbf_hours": 160,
                    "mttr_hours": 1.7,
                    "pm_cycle_hours": 170,
                    "cost_of_downtime_eur_h": 1680,
                    "replacement_value_eur": 238000,
                    "recommended_spares_eur": 11000,
                    "monthly_contract_eur": 1480,
                    "service_levers": ["Evol synchronization", "pattern stability", "predictive wear"],
                },
                {
                    "id": "site3_hdp_02",
                    "name": "Heavy Duty Palletizer B",
                    "family_group": "palletizer",
                    "nominal_throughput_per_hour": 70,
                    "nominal_cycle_seconds": 50,
                    "energy_kw": 47,
                    "temperature_base_c": 40,
                    "vibration_base_mm_s": 2.2,
                    "mtbf_hours": 162,
                    "mttr_hours": 1.6,
                    "pm_cycle_hours": 170,
                    "cost_of_downtime_eur_h": 1680,
                    "replacement_value_eur": 238000,
                    "recommended_spares_eur": 11000,
                    "monthly_contract_eur": 1480,
                    "service_levers": ["load balancing", "interlayer stability", "recipe governance"],
                },
            ],
        },
        {
            "id": "4",
            "name": "IP Piscataway",
            "country": "USA",
            "summary": "Gestión intralogística con AMRs en zona corrugadora y conversión, con tridentes, pesaje, scrap, interlayers y mandrinos.",
            "equipment": [
                {
                    "id": "site4_amr_corr_01",
                    "name": "AMR Corrugator Zone",
                    "family_group": "amr",
                    "nominal_throughput_per_hour": 24,
                    "nominal_cycle_seconds": 148,
                    "energy_kw": 9,
                    "temperature_base_c": 29,
                    "vibration_base_mm_s": 0.9,
                    "mtbf_hours": 220,
                    "mttr_hours": 1.0,
                    "pm_cycle_hours": 190,
                    "cost_of_downtime_eur_h": 780,
                    "replacement_value_eur": 98000,
                    "recommended_spares_eur": 5100,
                    "monthly_contract_eur": 890,
                    "service_levers": ["battery orchestration", "scrap routes", "mandrel logistics"],
                },
                {
                    "id": "site4_amr_conv_01",
                    "name": "AMR Converting 1",
                    "family_group": "amr",
                    "nominal_throughput_per_hour": 19,
                    "nominal_cycle_seconds": 188,
                    "energy_kw": 8,
                    "temperature_base_c": 28,
                    "vibration_base_mm_s": 0.8,
                    "mtbf_hours": 214,
                    "mttr_hours": 1.0,
                    "pm_cycle_hours": 190,
                    "cost_of_downtime_eur_h": 860,
                    "replacement_value_eur": 98000,
                    "recommended_spares_eur": 5100,
                    "monthly_contract_eur": 890,
                    "service_levers": ["interlayer supply", "scrap removal", "task balancing"],
                },
                {
                    "id": "site4_amr_conv_02",
                    "name": "AMR Converting 2",
                    "family_group": "amr",
                    "nominal_throughput_per_hour": 19,
                    "nominal_cycle_seconds": 188,
                    "energy_kw": 8,
                    "temperature_base_c": 28,
                    "vibration_base_mm_s": 0.8,
                    "mtbf_hours": 214,
                    "mttr_hours": 1.0,
                    "pm_cycle_hours": 190,
                    "cost_of_downtime_eur_h": 860,
                    "replacement_value_eur": 98000,
                    "recommended_spares_eur": 5100,
                    "monthly_contract_eur": 890,
                    "service_levers": ["interlayer supply", "scrap removal", "task balancing"],
                },
                {
                    "id": "site4_amr_conv_03",
                    "name": "AMR Converting 3",
                    "family_group": "amr",
                    "nominal_throughput_per_hour": 17,
                    "nominal_cycle_seconds": 212,
                    "energy_kw": 8,
                    "temperature_base_c": 28,
                    "vibration_base_mm_s": 0.8,
                    "mtbf_hours": 208,
                    "mttr_hours": 1.1,
                    "pm_cycle_hours": 190,
                    "cost_of_downtime_eur_h": 820,
                    "replacement_value_eur": 98000,
                    "recommended_spares_eur": 5100,
                    "monthly_contract_eur": 890,
                    "service_levers": ["small machines support", "auxiliary bundle moves", "interlayer service"],
                },
                {
                    "id": "site4_trident_01",
                    "name": "Trident Exchange Network",
                    "family_group": "conveyor",
                    "nominal_throughput_per_hour": 86,
                    "nominal_cycle_seconds": 26,
                    "energy_kw": 21,
                    "temperature_base_c": 33,
                    "vibration_base_mm_s": 1.6,
                    "mtbf_hours": 206,
                    "mttr_hours": 0.9,
                    "pm_cycle_hours": 174,
                    "cost_of_downtime_eur_h": 980,
                    "replacement_value_eur": 130000,
                    "recommended_spares_eur": 6300,
                    "monthly_contract_eur": 720,
                    "service_levers": ["handoff timing", "buffer slots", "priority exchange logic"],
                },
                {
                    "id": "site4_scale_01",
                    "name": "Weighing + Load Cell Station",
                    "family_group": "weighing",
                    "nominal_throughput_per_hour": 30,
                    "nominal_cycle_seconds": 120,
                    "energy_kw": 5,
                    "temperature_base_c": 27,
                    "vibration_base_mm_s": 0.7,
                    "mtbf_hours": 280,
                    "mttr_hours": 0.7,
                    "pm_cycle_hours": 220,
                    "cost_of_downtime_eur_h": 450,
                    "replacement_value_eur": 42000,
                    "recommended_spares_eur": 2400,
                    "monthly_contract_eur": 380,
                    "service_levers": ["weight traceability", "scrap analytics", "tare validation"],
                },
            ],
        },
        {
            "id": "5",
            "name": "Sterner Global-Mastercorr",
            "country": "USA",
            "summary": "Ingetrans para entrega y devolución de bobinas, 10 carriles, 5 portabobinas y estación RFID de almacén.",
            "equipment": [
                {
                    "id": "site5_ingetrans_01",
                    "name": "Ingetrans Rail Transfer",
                    "family_group": "ingetrans",
                    "nominal_throughput_per_hour": 15,
                    "nominal_cycle_seconds": 240,
                    "energy_kw": 18,
                    "temperature_base_c": 32,
                    "vibration_base_mm_s": 1.4,
                    "mtbf_hours": 236,
                    "mttr_hours": 1.1,
                    "pm_cycle_hours": 196,
                    "cost_of_downtime_eur_h": 1240,
                    "replacement_value_eur": 320000,
                    "recommended_spares_eur": 12800,
                    "monthly_contract_eur": 1360,
                    "service_levers": ["rail reservation", "reel traceability", "exchange sequencing"],
                },
                {
                    "id": "site5_grid_01",
                    "name": "10-Lane Reel Exchange Grid",
                    "family_group": "conveyor",
                    "nominal_throughput_per_hour": 42,
                    "nominal_cycle_seconds": 82,
                    "energy_kw": 14,
                    "temperature_base_c": 31,
                    "vibration_base_mm_s": 1.2,
                    "mtbf_hours": 244,
                    "mttr_hours": 0.9,
                    "pm_cycle_hours": 198,
                    "cost_of_downtime_eur_h": 960,
                    "replacement_value_eur": 155000,
                    "recommended_spares_eur": 7200,
                    "monthly_contract_eur": 780,
                    "service_levers": ["lane occupancy", "roll stand readiness", "exchange ETA"],
                },
                {
                    "id": "site5_rfid_01",
                    "name": "Warehouse RFID Station",
                    "family_group": "rfid",
                    "nominal_throughput_per_hour": 68,
                    "nominal_cycle_seconds": 52,
                    "energy_kw": 3,
                    "temperature_base_c": 26,
                    "vibration_base_mm_s": 0.4,
                    "mtbf_hours": 320,
                    "mttr_hours": 0.4,
                    "pm_cycle_hours": 240,
                    "cost_of_downtime_eur_h": 320,
                    "replacement_value_eur": 28000,
                    "recommended_spares_eur": 1900,
                    "monthly_contract_eur": 260,
                    "service_levers": ["warehouse reconciliation", "RFID health", "paper genealogy"],
                },
            ],
        },
    ],
}


def load_monitoring_blueprint() -> Dict[str, Any]:
    """Return the default monitoring blueprint with copy-on-read semantics."""
    return deepcopy(DEFAULT_BLUEPRINT)


def get_scope_options(blueprint: Dict[str, Any] | None = None) -> List[str]:
    loaded = blueprint or load_monitoring_blueprint()
    return ["all"] + [site["id"] for site in loaded["sites"]]


def get_scope_label(site_scope: str, blueprint: Dict[str, Any]) -> str:
    if site_scope == "all":
        return "General · Todas las plantas"
    for site in blueprint["sites"]:
        if site["id"] == site_scope:
            return f'{site["id"]} · {site["name"]}'
    return site_scope


def _stable_seed(*parts: str) -> int:
    digest = hashlib.sha256("::".join(parts).encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _family_profile(family_group: str) -> Dict[str, float]:
    profiles = {
        "palletizer": {"blocked_prob": 0.035, "starve_prob": 0.020, "quality_base": 0.992, "health_decay": 1.05},
        "conveyor": {"blocked_prob": 0.048, "starve_prob": 0.012, "quality_base": 0.996, "health_decay": 0.85},
        "sheet_handoff": {"blocked_prob": 0.052, "starve_prob": 0.030, "quality_base": 0.994, "health_decay": 0.95},
        "truck_loader": {"blocked_prob": 0.030, "starve_prob": 0.010, "quality_base": 0.997, "health_decay": 0.90},
        "amr": {"blocked_prob": 0.018, "starve_prob": 0.020, "quality_base": 0.998, "health_decay": 0.75},
        "weighing": {"blocked_prob": 0.010, "starve_prob": 0.005, "quality_base": 0.999, "health_decay": 0.55},
        "ingetrans": {"blocked_prob": 0.024, "starve_prob": 0.016, "quality_base": 0.998, "health_decay": 0.80},
        "rfid": {"blocked_prob": 0.006, "starve_prob": 0.000, "quality_base": 0.999, "health_decay": 0.40},
    }
    return profiles.get(family_group, profiles["conveyor"])


def _iter_timestamps(now: datetime, days: int, interval_minutes: int) -> Iterable[datetime]:
    anchor = now.replace(second=0, microsecond=0)
    anchor = anchor - timedelta(minutes=anchor.minute % interval_minutes)
    start = anchor - timedelta(days=days)
    total_steps = int((days * 24 * 60) / interval_minutes) + 1
    for step in range(total_steps):
        yield start + timedelta(minutes=step * interval_minutes)


def _shift_for(ts: datetime, blueprint: Dict[str, Any]) -> Dict[str, Any]:
    hour = ts.hour
    for shift in blueprint["shift_model"]:
        start = shift["start_hour"]
        end = shift["end_hour"]
        if start < end and start <= hour < end:
            return shift
        if start > end and (hour >= start or hour < end):
            return shift
    return blueprint["shift_model"][0]


def _simulate_equipment(
    site: Dict[str, Any],
    equipment: Dict[str, Any],
    now: datetime,
    days: int,
    interval_minutes: int,
    blueprint: Dict[str, Any],
) -> List[Dict[str, Any]]:
    rng = random.Random(_stable_seed(site["id"], equipment["id"], now.strftime("%Y%m%d")))
    family = equipment["family_group"]
    family_profile = _family_profile(family)
    interval_hours = interval_minutes / 60.0
    nominal = float(equipment["nominal_throughput_per_hour"])
    pm_cycle_hours = float(equipment["pm_cycle_hours"])
    runtime_since_pm = rng.uniform(0.18, 0.78) * pm_cycle_hours
    downtime_window_remaining_h = 0.0
    battery_pct = rng.uniform(58.0, 92.0)
    position_index = int(rng.uniform(1, 10))
    rows: List[Dict[str, Any]] = []

    for idx, ts in enumerate(_iter_timestamps(now, days, interval_minutes)):
        shift = _shift_for(ts, blueprint)
        holiday = ts.weekday() == int(blueprint["holiday_weekday"])
        scheduled = not holiday
        maintenance_window = holiday and 7 <= ts.hour < 11
        phase = math.sin((idx / 96.0) * math.pi * 2.0 + rng.random())
        load_factor = 0.93 + max(0.0, phase) * 0.09
        shift_factor = float(shift["performance_factor"])
        health_drift = min(0.26, (runtime_since_pm / max(pm_cycle_hours, 1.0)) * 0.22 * family_profile["health_decay"])
        temp_c = float(equipment["temperature_base_c"]) + (6.5 * load_factor) + (health_drift * 20) + rng.uniform(-0.9, 0.9)
        vibration = float(equipment["vibration_base_mm_s"]) + (health_drift * 2.1) + rng.uniform(-0.15, 0.2)
        predicted_failure = min(98.0, 22.0 + (runtime_since_pm / max(pm_cycle_hours, 1.0)) * 58.0 + (max(0.0, vibration - equipment["vibration_base_mm_s"]) * 11.0))
        queue_pct = min(100.0, 22.0 + max(0.0, phase) * 42.0 + rng.uniform(-6.0, 8.0))

        if downtime_window_remaining_h > 0:
            state = "breakdown"
            downtime_window_remaining_h = max(0.0, downtime_window_remaining_h - interval_hours)
        elif maintenance_window:
            state = "planned_maintenance"
            runtime_since_pm = max(0.0, runtime_since_pm - (interval_hours * 8.0))
        elif not scheduled:
            state = "holiday"
        else:
            failure_prob = interval_hours / max(float(equipment["mtbf_hours"]), 1.0)
            failure_prob *= 1.0 + max(0.0, predicted_failure - 55.0) / 120.0
            blocked_prob = family_profile["blocked_prob"] * (1.0 + queue_pct / 180.0)
            starve_prob = family_profile["starve_prob"] * (1.0 + max(0.0, 55.0 - queue_pct) / 220.0)
            if family == "amr" and battery_pct < 22.0:
                state = "charging"
            else:
                draw = rng.random()
                if draw < failure_prob:
                    downtime_window_remaining_h = float(equipment["mttr_hours"]) * rng.uniform(0.85, 1.35)
                    state = "breakdown"
                elif draw < failure_prob + blocked_prob:
                    state = "blocked"
                elif draw < failure_prob + blocked_prob + starve_prob:
                    state = "starved"
                else:
                    state = "running"

        availability = {
            "running": 1.0,
            "blocked": 0.72,
            "starved": 0.55,
            "charging": 0.35,
            "breakdown": 0.0,
            "planned_maintenance": 0.0,
            "holiday": 0.0,
        }.get(state, 0.0)
        performance = 0.0
        if state == "running":
            performance = max(0.70, min(1.03, load_factor * shift_factor * (1.0 - health_drift) + rng.uniform(-0.05, 0.03)))
        elif state == "blocked":
            performance = max(0.32, min(0.72, 0.58 * shift_factor + rng.uniform(-0.04, 0.05)))
        elif state == "starved":
            performance = max(0.24, min(0.64, 0.48 * shift_factor + rng.uniform(-0.03, 0.04)))
        elif state == "charging":
            performance = 0.14

        quality = family_profile["quality_base"]
        quality -= max(0.0, (predicted_failure - 70.0) / 4000.0)
        quality -= max(0.0, queue_pct - 75.0) / 6000.0
        quality = max(0.955, min(0.999, quality + rng.uniform(-0.0025, 0.0015)))

        throughput = nominal * performance if scheduled else 0.0
        energy_kw = 0.0 if state in {"holiday", "planned_maintenance"} else float(equipment["energy_kw"]) * max(0.18, performance + availability * 0.35)
        alarm_count = 0
        if state == "breakdown":
            alarm_count = 3
        elif state in {"blocked", "starved"}:
            alarm_count = 2
        elif predicted_failure >= 82:
            alarm_count = 1

        if family == "amr":
            if state == "charging":
                battery_pct = min(100.0, battery_pct + interval_hours * 20.0)
            elif state in {"running", "blocked", "starved"}:
                battery_pct = max(9.0, battery_pct - interval_hours * (8.0 if state == "running" else 5.5))
            else:
                battery_pct = min(100.0, battery_pct + interval_hours * 1.2)
        else:
            battery_pct = None  # type: ignore[assignment]

        if family in {"ingetrans", "conveyor", "sheet_handoff", "truck_loader"}:
            position_index = 1 + ((position_index + int(performance * 10) + idx) % 10)

        runtime_since_pm += interval_hours if state in {"running", "blocked", "starved", "charging"} else 0.0
        maintenance_due_days = round((pm_cycle_hours - runtime_since_pm) / 24.0, 1)
        pm_compliance_pct = max(0.0, min(100.0, 100.0 * max(0.0, 1.0 - max(0.0, runtime_since_pm - pm_cycle_hours) / max(pm_cycle_hours, 1.0))))
        health_score = max(1.0, min(100.0, 100.0 - (predicted_failure * 0.55) - (max(0.0, vibration - equipment["vibration_base_mm_s"]) * 7.0)))
        alarm_density = min(100.0, alarm_count * 30.0)
        lpi_pct = min(100.0, (queue_pct * 0.45) + (alarm_density * 0.30) + (predicted_failure * 0.25))
        operator_calls_open = 1 if state in {"blocked", "breakdown"} and rng.random() > 0.38 else 0
        intervention_queue = 1 if state == "breakdown" or predicted_failure >= 84.0 else 0

        row = {
            "timestamp": ts.isoformat(),
            "site_id": site["id"],
            "site_name": site["name"],
            "equipment_id": equipment["id"],
            "equipment_name": equipment["name"],
            "family_group": family,
            "state": state,
            "shift": shift["name"],
            "scheduled": scheduled,
            "holiday": holiday,
            "throughput_per_hour": round(throughput, 2),
            "nominal_throughput_per_hour": nominal,
            "availability_pct": round(availability * 100.0, 2),
            "performance_pct": round(performance * 100.0, 2),
            "quality_pct": round(quality * 100.0, 2),
            "oee_pct": round(availability * performance * quality * 100.0, 2),
            "energy_kw": round(energy_kw, 2),
            "temperature_c": round(temp_c, 2),
            "vibration_mm_s": round(vibration, 2),
            "queue_pct": round(queue_pct, 2),
            "lpi_pct": round(lpi_pct, 2),
            "alarm_count": alarm_count,
            "predicted_failure_risk_pct": round(predicted_failure, 2),
            "maintenance_due_days": maintenance_due_days,
            "runtime_since_pm_h": round(runtime_since_pm, 2),
            "pm_cycle_h": pm_cycle_hours,
            "pm_compliance_pct": round(pm_compliance_pct, 2),
            "health_score": round(health_score, 2),
            "operator_calls_open": operator_calls_open,
            "intervention_queue": intervention_queue,
            "cost_of_downtime_eur_h": equipment["cost_of_downtime_eur_h"],
            "replacement_value_eur": equipment["replacement_value_eur"],
            "recommended_spares_eur": equipment["recommended_spares_eur"],
            "monthly_contract_eur": equipment["monthly_contract_eur"],
            "service_levers": ", ".join(equipment["service_levers"]),
            "battery_pct": round(float(battery_pct), 2) if battery_pct is not None else None,
            "missions_per_hour": round(throughput * 0.95, 2) if family == "amr" else None,
            "scrap_kg_h": round(throughput * 19.0, 2) if family == "amr" else None,
            "interlayer_loads_h": round(max(0.0, throughput * 0.68), 2) if family in {"amr", "palletizer"} else None,
            "charger_occupancy_pct": round(max(0.0, 100.0 - float(battery_pct)) * 0.9, 2) if family == "amr" and battery_pct is not None else None,
            "reel_moves_h": round(throughput, 2) if family == "ingetrans" else None,
            "track_occupancy_pct": round(min(100.0, 38.0 + queue_pct * 0.52), 2) if family in {"ingetrans", "conveyor"} else None,
            "rfid_reads_h": round(throughput * 1.15, 2) if family == "rfid" else None,
            "transfer_position_index": position_index if family in {"ingetrans", "conveyor", "sheet_handoff", "truck_loader"} else None,
        }
        rows.append(row)
    return rows


def _latest_rows(series: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    latest: Dict[str, Dict[str, Any]] = {}
    for row in series:
        latest[row["equipment_id"]] = row
    return sorted(latest.values(), key=lambda row: (row["site_id"], row["equipment_name"]))


def _mean(values: Iterable[float]) -> float:
    values_list = [value for value in values if value is not None]
    if not values_list:
        return 0.0
    return sum(values_list) / len(values_list)


def _build_site_summaries(
    blueprint: Dict[str, Any],
    selected_sites: List[Dict[str, Any]],
    series: List[Dict[str, Any]],
    latest_assets: List[Dict[str, Any]],
    interval_minutes: int,
) -> List[Dict[str, Any]]:
    interval_hours = interval_minutes / 60.0
    site_rows: List[Dict[str, Any]] = []
    for site in selected_sites:
        site_series = [row for row in series if row["site_id"] == site["id"]]
        site_latest = [row for row in latest_assets if row["site_id"] == site["id"]]
        scheduled_rows = [row for row in site_series if row["scheduled"]]
        downtime_hours = sum(interval_hours for row in scheduled_rows if row["state"] in {"breakdown", "planned_maintenance"})
        energy_mwh_week = sum(float(row["energy_kw"]) * interval_hours for row in site_series) / 1000.0
        avg_cost = _mean(float(row["cost_of_downtime_eur_h"]) for row in site_latest)
        oee_gap = max(0.0, 85.0 - _mean(float(row["oee_pct"]) for row in scheduled_rows))
        annual_recovery_potential = oee_gap / 100.0 * max(avg_cost, 1.0) * 24.0 * 6.0 * 50.0 * 0.38
        site_rows.append(
            {
                "site_id": site["id"],
                "site_name": site["name"],
                "country": site["country"],
                "assets": len(site["equipment"]),
                "oee_pct": round(_mean(float(row["oee_pct"]) for row in scheduled_rows), 2),
                "availability_pct": round(_mean(float(row["availability_pct"]) for row in scheduled_rows), 2),
                "performance_pct": round(_mean(float(row["performance_pct"]) for row in scheduled_rows), 2),
                "quality_pct": round(_mean(float(row["quality_pct"]) for row in scheduled_rows), 2),
                "lpi_pct": round(_mean(float(row["lpi_pct"]) for row in scheduled_rows), 2),
                "critical_assets": sum(1 for row in site_latest if row["state"] == "breakdown" or float(row["predicted_failure_risk_pct"]) >= 86.0),
                "pm_due_assets": sum(1 for row in site_latest if float(row["maintenance_due_days"]) <= 3.0),
                "open_operator_calls": sum(int(row["operator_calls_open"]) for row in site_latest),
                "intervention_requests": sum(1 for row in site_latest if int(row["intervention_queue"]) > 0),
                "hidden_issue_count": sum(1 for row in site_latest if float(row["predicted_failure_risk_pct"]) >= 80.0 and int(row["operator_calls_open"]) == 0),
                "downtime_hours_week": round(downtime_hours, 2),
                "energy_mwh_week": round(energy_mwh_week, 2),
                "annual_recovery_potential_eur": round(annual_recovery_potential, 0),
                "summary": site["summary"],
            }
        )
    return site_rows


def _build_alerts(latest_assets: List[Dict[str, Any]], role: str) -> List[Dict[str, Any]]:
    alerts: List[Dict[str, Any]] = []
    for row in latest_assets:
        severity = None
        message = None
        if row["state"] == "breakdown":
            severity = "critical"
            message = "Parada no planificada activa."
        elif float(row["predicted_failure_risk_pct"]) >= 88.0:
            severity = "high"
            message = "Riesgo de avería inminente por tendencia de condición."
        elif float(row["maintenance_due_days"]) <= 0.0:
            severity = "high"
            message = "Preventivo vencido."
        elif float(row["oee_pct"]) <= 58.0:
            severity = "medium"
            message = "OEE por debajo del umbral operativo."
        elif row.get("battery_pct") is not None and float(row["battery_pct"]) <= 20.0:
            severity = "medium"
            message = "Batería AMR crítica."
        if severity:
            alerts.append(
                {
                    "severity": severity,
                    "site_name": row["site_name"],
                    "equipment_name": row["equipment_name"],
                    "state": row["state"],
                    "message": message,
                    "detected_by": "AI copilot" if role == "Ingecart" and int(row["operator_calls_open"]) == 0 else "Operations layer",
                }
            )
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return sorted(alerts, key=lambda item: (severity_order.get(item["severity"], 9), item["site_name"], item["equipment_name"]))


def _build_hidden_issues(latest_assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    issues = []
    for row in latest_assets:
        if float(row["predicted_failure_risk_pct"]) >= 80.0 and int(row["operator_calls_open"]) == 0:
            issues.append(
                {
                    "site_name": row["site_name"],
                    "equipment_name": row["equipment_name"],
                    "issue": "Riesgo latente detectado sin ticket abierto.",
                    "evidence": f'health={row["health_score"]} | risk={row["predicted_failure_risk_pct"]}% | alarms={row["alarm_count"]}',
                }
            )
    return issues


def _build_recommendations(site_summaries: List[Dict[str, Any]], latest_assets: List[Dict[str, Any]], role: str) -> List[Dict[str, Any]]:
    recs: List[Dict[str, Any]] = []
    latest_by_site: Dict[str, List[Dict[str, Any]]] = {}
    for row in latest_assets:
        latest_by_site.setdefault(row["site_id"], []).append(row)

    for summary in site_summaries:
        site_id = summary["site_id"]
        site_assets = latest_by_site.get(site_id, [])
        if summary["oee_pct"] < 75.0:
            recs.append(
                {
                    "site_id": site_id,
                    "site_name": summary["site_name"],
                    "title": "Recuperar OEE de la planta",
                    "action": "Atacar pérdidas dominantes con secuenciación dinámica, mantenimiento preventivo y ajuste de handoffs.",
                    "estimated_oee_gain_pct": round(min(8.5, max(2.5, (75.0 - summary["oee_pct"]) * 0.45)), 1),
                    "business_value_eur_year": round(summary["annual_recovery_potential_eur"] * 0.55, 0),
                }
            )
        if site_id == "2":
            recs.append(
                {
                    "site_id": site_id,
                    "site_name": summary["site_name"],
                    "title": "Sincronizar BHS, transfercar y bottom/tie sheets",
                    "action": "Añadir reserva de destino, disponibilidad de Kuka pallet y prioridad dinámica en el handoff BHS-Ingecart.",
                    "estimated_oee_gain_pct": 3.8,
                    "business_value_eur_year": 132000,
                }
            )
        if site_id == "4":
            recs.append(
                {
                    "site_id": site_id,
                    "site_name": summary["site_name"],
                    "title": "Balancear flota AMR de converting",
                    "action": "Reequilibrar las tres zonas de intercambio y anticipar ventanas de carga de baterías.",
                    "estimated_oee_gain_pct": 4.6,
                    "business_value_eur_year": 158000,
                }
            )
        if site_id == "5":
            recs.append(
                {
                    "site_id": site_id,
                    "site_name": summary["site_name"],
                    "title": "Cerrar lazo Ingetrans + RFID",
                    "action": "Cruzar ocupación de carriles, readiness de portabobinas y lecturas RFID para evitar búsquedas y devoluciones erróneas.",
                    "estimated_oee_gain_pct": 3.1,
                    "business_value_eur_year": 97000,
                }
            )
        if site_id == "3":
            hdp_assets = [asset for asset in site_assets if asset["family_group"] == "palletizer"]
            if len(hdp_assets) == 2:
                asymmetry = abs(float(hdp_assets[0]["oee_pct"]) - float(hdp_assets[1]["oee_pct"]))
                if asymmetry >= 4.0:
                    recs.append(
                        {
                            "site_id": site_id,
                            "site_name": summary["site_name"],
                            "title": "Balancear doble paletizador Mitsubishi Evol",
                            "action": "Nivelar recetas, ventanas de cambio y share de carga entre ambos paletizadores.",
                            "estimated_oee_gain_pct": round(min(5.5, asymmetry * 0.6), 1),
                            "business_value_eur_year": 112000,
                        }
                    )

    if role == "Ingecart":
        for hidden in _build_hidden_issues(latest_assets):
            recs.append(
                {
                    "site_id": None,
                    "site_name": hidden["site_name"],
                    "title": f'Activar intervención proactiva en {hidden["equipment_name"]}',
                    "action": hidden["issue"],
                    "estimated_oee_gain_pct": 1.8,
                    "business_value_eur_year": 48000,
                }
            )
    return recs


def _build_interventions(latest_assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    items = []
    for row in latest_assets:
        if row["state"] == "breakdown" or float(row["predicted_failure_risk_pct"]) >= 76.0:
            priority = "critical" if row["state"] == "breakdown" or float(row["predicted_failure_risk_pct"]) >= 88.0 else "high"
            items.append(
                {
                    "site_name": row["site_name"],
                    "equipment_name": row["equipment_name"],
                    "priority": priority,
                    "request_type": "corrective" if row["state"] == "breakdown" else "condition-based",
                    "sla_hours": 4 if priority == "critical" else 8,
                    "risk_pct": row["predicted_failure_risk_pct"],
                    "estimated_cost_eur": round(float(row["cost_of_downtime_eur_h"]) * (2.4 if priority == "critical" else 1.4), 0),
                }
            )
    return sorted(items, key=lambda item: (0 if item["priority"] == "critical" else 1, item["site_name"]))


def _build_contracts(site_summaries: List[Dict[str, Any]], latest_assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    leads = []
    for summary in site_summaries:
        site_assets = [row for row in latest_assets if row["site_id"] == summary["site_id"]]
        monthly = sum(float(row["monthly_contract_eur"]) for row in site_assets)
        if summary["critical_assets"] or summary["pm_due_assets"] >= 2 or summary["oee_pct"] < 76.0:
            leads.append(
                {
                    "site_name": summary["site_name"],
                    "scope": "Full coverage 24/7" if summary["critical_assets"] else "Preventive + remote diagnostics",
                    "monthly_value_eur": round(monthly * (1.35 if summary["critical_assets"] else 1.0), 0),
                    "focus": "Condition monitoring, PM compliance, spare readiness",
                }
            )
    return leads


def _build_material_recommendations(latest_assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    items = []
    for row in latest_assets:
        if float(row["predicted_failure_risk_pct"]) >= 70.0 or float(row["maintenance_due_days"]) <= 4.0:
            items.append(
                {
                    "site_name": row["site_name"],
                    "equipment_name": row["equipment_name"],
                    "recommended_spares_eur": row["recommended_spares_eur"],
                    "reason": "riesgo alto" if float(row["predicted_failure_risk_pct"]) >= 70.0 else "preventivo próximo",
                }
            )
    return items


def _build_portfolio(site_summaries: List[Dict[str, Any]], alerts: List[Dict[str, Any]], contracts: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "oee_pct": round(_mean(float(site["oee_pct"]) for site in site_summaries), 2),
        "availability_pct": round(_mean(float(site["availability_pct"]) for site in site_summaries), 2),
        "performance_pct": round(_mean(float(site["performance_pct"]) for site in site_summaries), 2),
        "quality_pct": round(_mean(float(site["quality_pct"]) for site in site_summaries), 2),
        "energy_mwh_week": round(sum(float(site["energy_mwh_week"]) for site in site_summaries), 2),
        "annual_recovery_potential_eur": round(sum(float(site["annual_recovery_potential_eur"]) for site in site_summaries), 0),
        "critical_assets": sum(int(site["critical_assets"]) for site in site_summaries),
        "active_alerts": len(alerts),
        "service_opportunity_eur": round(sum(float(item["monthly_value_eur"]) for item in contracts) * 12.0, 0),
    }


def build_meeting_report(snapshot: Dict[str, Any]) -> str:
    portfolio = snapshot["portfolio"]
    role_panel = snapshot["role_panel"]
    scope_label = snapshot["scope_label"]
    top_sites = snapshot["site_summaries"][:3]
    lines = [
        f"# Informe automático · {scope_label}",
        "",
        f"**Rol objetivo:** {snapshot['role']}",
        f"**Enfoque del panel:** {role_panel['description']}",
        f"**Stack recomendado:** {snapshot['blueprint']['recommended_stack']}",
        "",
        "## Resumen ejecutivo",
        f"- OEE portfolio: **{portfolio['oee_pct']}%**",
        f"- Disponibilidad: **{portfolio['availability_pct']}%**",
        f"- Alertas activas: **{portfolio['active_alerts']}**",
        f"- Potencial anual recuperable: **EUR {portfolio['annual_recovery_potential_eur']:.0f}**",
        "",
        "## Plantas prioritarias",
    ]
    for site in top_sites:
        lines.append(
            f"- **{site['site_id']} · {site['site_name']}**: OEE {site['oee_pct']}%, "
            f"activos críticos {site['critical_assets']}, PM próximas {site['pm_due_assets']}."
        )
    if snapshot["alerts"]:
        lines.extend(["", "## Alertas", *[
            f"- [{alert['severity']}] {alert['site_name']} · {alert['equipment_name']}: {alert['message']}"
            for alert in snapshot["alerts"][:6]
        ]])
    if snapshot["recommendations"]:
        lines.extend(["", "## Recomendaciones", *[
            f"- **{item['title']}** ({item['site_name']}): {item['action']} · impacto OEE +{item['estimated_oee_gain_pct']} pts"
            for item in snapshot["recommendations"][:6]
        ]])
    lines.extend([
        "",
        "## Documentos sugeridos",
        *[f"- {doc}" for doc in role_panel["documents"]],
    ])
    return "\n".join(lines)


def generate_monitoring_snapshot(
    site_scope: str = "all",
    role: str = "Ingecart",
    now: datetime | None = None,
    days: int = 7,
    interval_minutes: int = 15,
    blueprint: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    loaded_blueprint = blueprint or load_monitoring_blueprint()
    role_panel = ROLE_PANELS.get(role, ROLE_PANELS["Ingecart"])
    current_time = now or datetime.now()
    selected_sites = loaded_blueprint["sites"] if site_scope == "all" else [site for site in loaded_blueprint["sites"] if site["id"] == str(site_scope)]

    series: List[Dict[str, Any]] = []
    for site in selected_sites:
        for equipment in site["equipment"]:
            series.extend(_simulate_equipment(site, equipment, current_time, days, interval_minutes, loaded_blueprint))

    latest_assets = _latest_rows(series)
    site_summaries = _build_site_summaries(loaded_blueprint, selected_sites, series, latest_assets, interval_minutes)
    alerts = _build_alerts(latest_assets, role)
    hidden_issues = _build_hidden_issues(latest_assets)
    interventions = _build_interventions(latest_assets)
    contracts = _build_contracts(site_summaries, latest_assets)
    materials = _build_material_recommendations(latest_assets)
    recommendations = _build_recommendations(site_summaries, latest_assets, role)
    portfolio = _build_portfolio(site_summaries, alerts, contracts)

    snapshot = {
        "blueprint": loaded_blueprint,
        "scope_label": get_scope_label(site_scope, loaded_blueprint),
        "role": role,
        "role_panel": role_panel,
        "series": series,
        "equipment_latest": latest_assets,
        "site_summaries": site_summaries,
        "alerts": alerts,
        "hidden_issues": hidden_issues,
        "interventions": interventions,
        "contracts": contracts,
        "materials": materials,
        "recommendations": recommendations,
        "portfolio": portfolio,
        "formula_library": FORMULA_LIBRARY,
        "generated_at": current_time.isoformat(),
        "simulation_assumptions": {
            "days": days,
            "interval_minutes": interval_minutes,
            "shift_count": 3,
            "holiday_per_week": 1,
        },
    }
    snapshot["report_markdown"] = build_meeting_report(snapshot)
    return snapshot


def generate_instant_offer(
    snapshot: Dict[str, Any],
    request_kind: str,
    target_equipment_id: str = "all",
    coverage: str = "24x7",
    urgency: str = "priority",
) -> Dict[str, Any]:
    coverage_factor = {"business_hours": 1.0, "extended": 1.18, "24x7": 1.35}.get(coverage, 1.0)
    urgency_factor = {"standard": 1.0, "priority": 1.12, "emergency": 1.28}.get(urgency, 1.0)
    assets = snapshot["equipment_latest"]
    if target_equipment_id != "all":
        assets = [row for row in assets if row["equipment_id"] == target_equipment_id]
    if not assets:
        assets = snapshot["equipment_latest"]

    reference = f'ING-MON-{datetime.now():%Y%m%d}-{_stable_seed(request_kind, snapshot["scope_label"]) % 1000:03d}'
    lines = []
    total_capex = 0.0
    total_monthly = 0.0

    for asset in assets:
        risk_factor = 1.0 + max(0.0, float(asset["predicted_failure_risk_pct"]) - 60.0) / 220.0
        if request_kind == "maintenance_contract":
            monthly = float(asset["monthly_contract_eur"]) * coverage_factor * risk_factor
            lines.append({"concept": f'Servicio {asset["equipment_name"]}', "type": "monthly", "value_eur": round(monthly, 0)})
            total_monthly += monthly
        elif request_kind == "materials_and_spares":
            capex = float(asset["recommended_spares_eur"]) * urgency_factor * risk_factor
            lines.append({"concept": f'Repuestos {asset["equipment_name"]}', "type": "one-off", "value_eur": round(capex, 0)})
            total_capex += capex
        elif request_kind == "improvement_upgrade":
            capex = float(asset["replacement_value_eur"]) * 0.09 * risk_factor
            lines.append({"concept": f'Upgrade analítica + control {asset["equipment_name"]}', "type": "one-off", "value_eur": round(capex, 0)})
            total_capex += capex
        else:
            capex = float(asset["cost_of_downtime_eur_h"]) * (2.2 if urgency == "emergency" else 1.5) * risk_factor
            lines.append({"concept": f'Intervención {asset["equipment_name"]}', "type": "one-off", "value_eur": round(capex, 0)})
            total_capex += capex

    return {
        "reference": reference,
        "scope": snapshot["scope_label"],
        "request_kind": request_kind,
        "coverage": coverage,
        "urgency": urgency,
        "response_sla_hours": 4 if urgency == "emergency" else (8 if urgency == "priority" else 24),
        "lines": lines,
        "capex_total_eur": round(total_capex, 0),
        "monthly_total_eur": round(total_monthly, 0),
        "notes": [
            "Oferta inmediata orientativa generada desde criticidad, riesgo y parque instalado.",
            "Debe validarse contra layout final, lista de señales real y stock de repuestos.",
        ],
    }
