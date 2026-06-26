"""Validación headless rápida del motor CorrugatorEngine.

Ejecuta 100 pasos y muestra los KPIs resultantes.
"""
from __future__ import annotations

import json

import os
import sys

# ensure repo root is on sys.path when running this script directly
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.corrugator_engine import CorrugatorEngine


def main():
    config = {"corrugator_speed_m_min": 250, "num_tracks": 10, "buffer_capacity": 20}
    engine = CorrugatorEngine("A", config, seed=1)
    engine.running = True
    for _ in range(100):
        engine.step()
    kpis = engine.get_kpis()
    print("✅ Validación completada")
    print(json.dumps(kpis, indent=2))


if __name__ == "__main__":
    main()
