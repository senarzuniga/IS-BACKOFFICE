from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Dict

from .models import OfferInput


def _read_source(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _extract_sr1400_core_spanish() -> str:
    base = Path("informes/ingecart-marketing-kit/ingecart-marketing-kit/content-kit")
    source = _read_source(base / "02-soluciones-catalogo.md")
    if "## 2. Sistema Retal SR1400" not in source:
        return "Sistema SR1400 para recogida y transporte integrado de retal con foco en eficiencia energética."
    start = source.index("## 2. Sistema Retal SR1400")
    end_marker = "## 3. IIM Rollstand"
    end = source.find(end_marker, start)
    if end == -1:
        end = len(source)
    return source[start:end].strip()


def build_knowledge_package(offer: OfferInput) -> Dict[str, Dict[str, str]]:
    sr1400_es = _extract_sr1400_core_spanish()

    executive_es = (
        "El SR1400 es una solucion proporcional de gestion de retal para plantas de corrugado "
        "que reduce consumo energetico, elimina intervenciones manuales repetitivas y aporta "
        "continuidad al flujo productivo."
    )
    executive_en = (
        "SR1400 is a proportional scrap-management solution for corrugated plants that reduces "
        "energy consumption, removes repetitive manual handling, and stabilizes production flow."
    )

    technical_es = (
        "El diseno del SR1400 se adapta al layout de planta, longitud de linea principal, giros y rampas. "
        "La arquitectura integra transporte continuo de retal, motorizacion distribuida y control electrico modular."
    )
    technical_en = (
        "SR1400 engineering adapts to plant layout, main-line length, turns, and ramps. "
        "The architecture integrates continuous scrap transport, distributed drives, and modular electrical control."
    )

    package = {
        "executive": {"es": executive_es, "en": executive_en},
        "technical_description": {"es": technical_es, "en": technical_en},
        "design_philosophy": {
            "es": "Diseno modular, escalable y proporcional al proceso real del cliente.",
            "en": "Modular, scalable design proportional to each customer process.",
        },
        "technical_differentiators": {
            "es": "Hasta 93% de reduccion energetica, integracion por fases y adaptacion completa al layout.",
            "en": "Up to 93% energy reduction, phased deployment, and full layout adaptation.",
        },
        "operational_benefits": {
            "es": "Menor coste operativo, menor acumulacion de retal y mayor seguridad operativa.",
            "en": "Lower operating cost, lower scrap accumulation, and improved operational safety.",
        },
        "tco": {
            "es": "ROI tipico entre 12 y 24 meses segun volumen y condiciones de operacion.",
            "en": "Typical ROI between 12 and 24 months depending on throughput and operations.",
        },
        "value_proposition": {
            "es": "Ingecart ofrece ingenieria independiente con responsabilidad integral del resultado.",
            "en": "Ingecart provides independent engineering with full outcome ownership.",
        },
        "conclusions": {
            "es": "SR1400 es la opcion estandar para reducir coste de retal con continuidad de proceso.",
            "en": "SR1400 is the standard option to reduce scrap cost while preserving process continuity.",
        },
        "source_sr1400_spanish": {"es": sr1400_es, "en": "Translated/adapted from internal Spanish base content."},
        "offer_context": asdict(offer),
    }
    return package
