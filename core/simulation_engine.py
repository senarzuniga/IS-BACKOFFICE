"""Motor de simulación base para Bobina Load Simulator.
Contiene la clase BaseSimulationEngine que gestiona la geometría común,
la cola de órdenes y el avance temporal.

Todas las distancias están en metros. El paso de simulación es 0.1 minutos (6 segundos).
"""

import time
import math
from typing import Dict, List, Any, Tuple


class BaseSimulationEngine:
    """Clase base que contiene geometría común y lógica de tiempos.

    Atributos principales:
    - layout: dict con elementos y coordenadas
    - orders: lista de órdenes de entrega de bobinas a tracks
    - config: parámetros del simulador (p.ej. n_vehicles)
    - time_min: tiempo simulado en minutos
    - step_min: incremento por paso en minutos (0.1)
    - entities: lista de agentes móviles (carretillas o transfer)
    - reels: estado de bobinas en almacén/tracks/buffer
    - metrics: acumuladores para KPIs
    """

    def __init__(self, layout: Dict[str, Any], orders: List[Dict[str, Any]], config: Dict[str, Any]):
        self.layout = layout
        self.orders = orders.copy()
        self.config = config
        self.time_min = 0.0
        self.step_min = 0.1  # 0.1 minutes = 6 seconds
        self.entities = []
        self.reels = {}  # key: reel_id -> location/status
        self.metrics = {
            "reel_changes": 0,
            "distance_m": 0.0,
            "starvations": 0,
            "downtime_min": 0.0,
            "utilization_time_min": {},  # entity_id -> minutes active
            "collisions": 0,
            "wait_time_min": 0.0,
        }
        self._init_layout()
        self._init_resources()

    def _init_layout(self):
        # Validar geometría mínima
        required = ["corrugator", "tracks", "warehouse"]
        for r in required:
            if r not in self.layout:
                raise ValueError(f"Layout missing required element: {r}")

    def _init_resources(self):
        # Crear estructuras para reels y entidades según layout
        # Inicializamos reels desde órdenes si se proveen
        for o in self.orders:
            rid = o.get("reel_id")
            if rid:
                self.reels[rid] = {"status": "in_warehouse", "pos": tuple(self.layout["warehouse"]["pos"])}

    def step(self):
        """Avanza la simulación en un paso de self.step_min minutos.
        Se espera que las subclases extiendan este método para implementar
        la lógica específica de movimiento y asignación.
        """
        self.time_min += self.step_min

    def get_state(self) -> Dict[str, Any]:
        """Devuelve el estado para renderizado: entidades, reels, tiempo.
        """
        return {
            "time_min": self.time_min,
            "entities": [e.copy() for e in self.entities],
            "reels": {k: v.copy() for k, v in self.reels.items()},
            "layout": self.layout,
        }

    def get_kpis(self) -> Dict[str, Any]:
        """Calcula y devuelve KPIs básicos.
        """
        utilization = {}
        for eid, t in self.metrics["utilization_time_min"].items():
            utilization[eid] = t / max(1.0, self.time_min) * 100.0

        return {
            "reel_changes_hour": self.metrics["reel_changes"] / max(1.0, self.time_min) * 60.0,
            "distance_m": self.metrics["distance_m"],
            "collisions": self.metrics["collisions"],
            "starvations": self.metrics["starvations"],
            "downtime_min": self.metrics["downtime_min"],
            "utilization": utilization,
            "wait_time_min": self.metrics["wait_time_min"],
        }

    # Métodos auxiliares de movimiento
    @staticmethod
    def _dist(a: Tuple[float, float], b: Tuple[float, float]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def move_entity_towards(self, entity: Dict[str, Any], target: Tuple[float, float], speed_m_per_min: float) -> None:
        """Mueve la entidad hacia target. Actualiza distancia recorrida y posición.

        entity: dict con 'pos':(x,y), 'id'
        target: (x,y)
        speed_m_per_min: metros por minuto
        """
        current = tuple(entity.get("pos", (0.0, 0.0)))
        max_dist = speed_m_per_min * self.step_min
        d = self._dist(current, target)
        if d <= 1e-6:
            entity["pos"] = target
            return
        ratio = min(1.0, max_dist / d)
        newx = current[0] + (target[0] - current[0]) * ratio
        newy = current[1] + (target[1] - current[1]) * ratio
        moved = self._dist(current, (newx, newy))
        entity["pos"] = (newx, newy)
        self.metrics["distance_m"] += moved
        # contabilizar utilización
        self.metrics["utilization_time_min"][entity["id"]] = self.metrics["utilization_time_min"].get(entity["id"], 0.0) + self.step_min

    # Eventos inyectables (interface)
    def inject_event(self, event_type: str, payload: Dict[str, Any] = None):
        """Registrar evento externo que modifique estado. Subclases deben manejar.
        """
        pass
