"""Equipment library — catalog of standard corrugated plant machines and their defaults."""
from __future__ import annotations

from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Corrugator Models
# ---------------------------------------------------------------------------

CORRUGATOR_CATALOG: List[Dict[str, Any]] = [
    {
        "brand": "BHS",
        "model": "OPTIFLEX 2.8",
        "width_mm": 2800,
        "speed_m_min": 400,
        "description": "Corrugadora de alta velocidad para producciones >200,000 m²/turno",
        "m2_per_shift_estimate": 192000,
        "notes": "Almacén bobinas doble enrollador recomendado. CABER + Vulcan splicer.",
    },
    {
        "brand": "BHS",
        "model": "CORRUGATOR 2.5",
        "width_mm": 2500,
        "speed_m_min": 300,
        "description": "Corrugadora estándar europea. La más extendida en España y sur de Europa.",
        "m2_per_shift_estimate": 144000,
        "notes": "Flujos estándar: B/C/BC. Almacén 80-120 bobinas suficiente.",
    },
    {
        "brand": "FOSBER",
        "model": "ULTIMA 2.5",
        "width_mm": 2500,
        "speed_m_min": 280,
        "description": "Corrugadora italiana. Alta flexibilidad de fluting. Presencia fuerte en Italia, España.",
        "m2_per_shift_estimate": 134400,
        "notes": "Changeover rápido B/C/E. Interface SmartBrain integrado.",
    },
    {
        "brand": "MITSUBISHI",
        "model": "H series 2.5",
        "width_mm": 2500,
        "speed_m_min": 350,
        "description": "Corrugadora japonesa de alta precisión. Baja tolerancia de vibración.",
        "m2_per_shift_estimate": 168000,
        "notes": "Baja tasa de scrap en arranque. Requiere personal especializado para mantenimiento.",
    },
    {
        "brand": "GENERIC",
        "model": "Estándar 2.2",
        "width_mm": 2200,
        "speed_m_min": 200,
        "description": "Corrugadora de media capacidad. Común en plantas medianas ibéricas.",
        "m2_per_shift_estimate": 96000,
        "notes": "Referencia base para plantas nuevas o en crecimiento.",
    },
]

# ---------------------------------------------------------------------------
# Converter Models
# ---------------------------------------------------------------------------

CONVERTER_CATALOG: List[Dict[str, Any]] = [
    {
        "type": "flexografica",
        "brand": "BOBST",
        "model": "EXPERTFOLD 110",
        "format_max_mm": [1100, 2000],
        "speed_uds_per_hour": 800,
        "description": "Pegadora-plegadora de alta gama. Ideal cajas automontables y RSC.",
        "setup_time_min": 20,
        "availability": 0.93,
    },
    {
        "type": "flexografica",
        "brand": "EMBA",
        "model": "EVOMARK 245",
        "format_max_mm": [1200, 2450],
        "speed_uds_per_hour": 1200,
        "description": "Flexográfica de imprimir-troquelar de alta velocidad. Ideal RSC y bandejas.",
        "setup_time_min": 25,
        "availability": 0.91,
    },
    {
        "type": "troqueladora",
        "brand": "BOBST",
        "model": "MASTERCUT 1.7",
        "format_max_mm": [1100, 1700],
        "speed_uds_per_hour": 1500,
        "description": "Troqueladora plana de alta velocidad. Para cajas de corte especial y displays.",
        "setup_time_min": 30,
        "availability": 0.90,
    },
    {
        "type": "troqueladora",
        "brand": "KASEMAKE",
        "model": "ADVANTAGE 240",
        "format_max_mm": [800, 1600],
        "speed_uds_per_hour": 900,
        "description": "Troqueladora digital para prototipos y tiradas cortas. Sin troquel físico.",
        "setup_time_min": 5,
        "availability": 0.95,
    },
    {
        "type": "rotativa",
        "brand": "WARD",
        "model": "760 ULTRASTACK",
        "format_max_mm": [900, 1900],
        "speed_uds_per_hour": 2000,
        "description": "Rotativa de alta velocidad con apilador automático. Para volúmenes RSC grandes.",
        "setup_time_min": 45,
        "availability": 0.88,
    },
    {
        "type": "flexografica",
        "brand": "CORRUGATED TECH",
        "model": "CT-900 Flexo",
        "format_max_mm": [900, 1800],
        "speed_uds_per_hour": 1000,
        "description": "Flexográfica media. Equilibrio entre coste y flexibilidad. Habitual en plantas medianas.",
        "setup_time_min": 30,
        "availability": 0.89,
    },
]

# ---------------------------------------------------------------------------
# Transport Equipment
# ---------------------------------------------------------------------------

TRANSPORT_CATALOG: List[Dict[str, Any]] = [
    {
        "type": "carretilla",
        "brand": "STILL",
        "model": "RX 60-30",
        "capacity_kg": 3000,
        "speed_ms": 2.0,
        "description": "Carretilla eléctrica contrapesada. Estándar en zonas de carga y almacén.",
        "cycle_time_min": 4,
    },
    {
        "type": "carretilla",
        "brand": "CROWN",
        "model": "FC 5252",
        "capacity_kg": 2500,
        "speed_ms": 1.8,
        "description": "Carretilla retráctil para pasillos estrechos. Ideal almacenes con pasillos <2.7m.",
        "cycle_time_min": 5,
    },
    {
        "type": "track",
        "brand": "MOVEX",
        "model": "TrackSystem 80",
        "speed_ms": 0.8,
        "description": "Track guiado automático para transporte de plano entre corrugadora y conversión.",
        "cycle_time_min": 2,
    },
    {
        "type": "conveyor",
        "brand": "INTRALOX",
        "model": "Series 1400",
        "speed_ms": 0.5,
        "description": "Conveyor modular de plástico. Para salidas de conversión hacia expedición.",
        "cycle_time_min": 1,
    },
    {
        "type": "agv",
        "brand": "KIVNON",
        "model": "K10 Pallet AGV",
        "capacity_kg": 1500,
        "speed_ms": 1.2,
        "description": "AGV autónomo para transporte de palets. Integración WMS. Sin conductor.",
        "cycle_time_min": 3,
    },
]

# ---------------------------------------------------------------------------
# Quick lookup helpers
# ---------------------------------------------------------------------------

def get_corrugator(model: str) -> Dict[str, Any]:
    for c in CORRUGATOR_CATALOG:
        if c["model"].lower() == model.lower():
            return c
    return CORRUGATOR_CATALOG[1]  # default BHS 2500


def get_converter(model: str) -> Dict[str, Any]:
    for c in CONVERTER_CATALOG:
        if c["model"].lower() == model.lower():
            return c
    return CONVERTER_CATALOG[0]


def get_default_corrugator() -> Dict[str, Any]:
    return CORRUGATOR_CATALOG[1]


def get_default_converters(n: int = 2) -> List[Dict[str, Any]]:
    base = [CONVERTER_CATALOG[1], CONVERTER_CATALOG[0]]
    result = []
    for i in range(n):
        item = dict(base[i % len(base)])
        item["id"] = f"C{i+1}"
        result.append(item)
    return result


# Efficiency benchmarks (sector industry data)
SECTOR_BENCHMARKS: Dict[str, float] = {
    "corrugator_oee": 0.82,
    "converter_oee": 0.78,
    "world_class_oee": 0.85,
    "transport_utilization": 0.65,
    "buffer_target_occupancy": 0.50,  # 50% fill = ideal flow balance
}
