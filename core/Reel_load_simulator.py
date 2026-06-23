"""Módulo principal del motor de simulación para el Reel Load Simulator.

Este motor es step-based (avanza por minutos). Es un modelo simplificado
pensado para prototipar la lógica de movimientos, cambios de Reel y métricas.
"""
from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class SimulationResult:
    sim_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    time_min: int = 0
    movements: int = 0
    reel_changes: int = 0
    starvation_events: int = 0
    downtime_min: int = 0
    utilization_pct: float = 0.0


class SimulationEngine:
    """Motor simplificado que almacena un `result` y avanza con `step()`.

    - `cfg` es el diccionario de configuración
    - `orders` es una lista de órdenes que alimentan producción
    - `scenario` es 'A' o 'B'
    """

    def __init__(self, cfg: Dict[str, Any], orders: List[Dict[str, Any]], scenario: str = "A") -> None:
        self.cfg = cfg
        self.orders = list(orders) if orders else []
        self.scenario = scenario
        self.time_min = 0
        self.result = SimulationResult()

        # parámetros sencillos
        self.speed_factor = 1.0 if scenario == "A" else 1.25

    def step(self) -> None:
        """Avanza la simulación un minuto y actualiza métricas simples."""
        self.time_min += 1
        # movimientos: aleatorio en función de scenario
        base_moves = random.randint(2, 6)
        moves = int(base_moves * (1.0 if self.scenario == "A" else 0.7))
        self.result.movements += moves

        # reel changes: cada X minutos
        if self.time_min % 12 == 0:
            self.result.reel_changes += 1 if self.scenario == "A" else 0

        # starvation event chance
        if random.random() < (0.03 if self.scenario == "A" else 0.01):
            self.result.starvation_events += 1

        # downtime
        if random.random() < 0.005:
            self.result.downtime_min += random.randint(1, 10)

        # utilization: heurístico simple
        self.result.utilization_pct = max(30.0, 95.0 - (self.result.movements % 50))

        # tiempo
        self.result.time_min = self.time_min

    def reset(self) -> None:
        self.time_min = 0
        self.result = SimulationResult()
