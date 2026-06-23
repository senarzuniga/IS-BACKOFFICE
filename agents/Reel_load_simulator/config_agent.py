"""Config Agent for Reel Load Simulator.

Gestiona la configuración de la planta y guarda/recupera JSON en `data/Reel_load_simulator`.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "Reel_load_simulator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT = {
    "corrugator_wet_end_m": 60,
    "num_spindles": 10,
    "num_tracks": 10,
    "conventional_num_forklifts": 2,
    "ingetrans_transfer_speed": 80,
}


class ConfigAgent:
    """Manejo simple de configuración: carga/guarda JSON."""

    def __init__(self, path: Path = DATA_DIR / "config_default.json") -> None:
        self.path = path
        if not self.path.exists():
            self.save_default(DEFAULT)

    def save_default(self, cfg: Dict[str, Any]) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)

    def load_default(self) -> Dict[str, Any]:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return dict(DEFAULT)
