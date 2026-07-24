from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict

from .models import OfferInput


def _load_formula_config() -> Dict:
    formula_path = Path(__file__).parent / "formulas" / "sr1400_formulas.json"
    return json.loads(formula_path.read_text(encoding="utf-8"))


def _compute_component_quantity(formula: Dict, offer: OfferInput) -> int:
    variables = {
        "line_length_m": float(offer.total_main_line_length_m),
        "turns_90": float(offer.turns_90),
        "ramps_count": float(offer.ramps_count),
        "ramp_length_m": float(offer.total_ramp_length_m),
    }
    total = float(formula.get("base", 0.0))
    for term in formula.get("terms", []):
        variable_name = term["variable"]
        coefficient = float(term.get("coefficient", 0.0))
        total += variables.get(variable_name, 0.0) * coefficient
    return int(math.ceil(max(total, 0.0)))


def calculate_sr1400_bom(offer: OfferInput) -> Dict[str, int]:
    cfg = _load_formula_config()
    out: Dict[str, int] = {}
    for component in cfg.get("components", []):
        out[component["name"]] = _compute_component_quantity(component["formula"], offer)
    return out
