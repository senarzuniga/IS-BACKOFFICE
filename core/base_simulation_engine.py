"""Motor base puro y testeable para el simulador de Bobina Load.

Contiene la clase `BaseSimulationEngine` usada por los motores específicos.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import threading
import statistics
import math


class BaseSimulationEngine:
    """Motor base: maneja tiempo, colas, órdenes, entidades y métricas.

    - `dt_min` : paso de simulación en minutos (1 segundo = 1/60 min)
    - `layout` : diccionario con geometría
    - `queue`  : lista de órdenes pendientes
    - `entities`: lista de agentes (dicts) manejados por subclases
    """

    def __init__(self, layout: Dict[str, Any], orders: Optional[List[Dict[str, Any]]] = None, config: Optional[Dict[str, Any]] = None, seed: Optional[int] = None):
        self.layout = layout
        self.config = config or {}
        # dt = 1 segundo = 1/60 minutes
        self.dt_min = 1.0 / 60.0
        # compatibilidad con código previo
        self.step_min = self.dt_min

        self.time_min = 0.0
        self.queue: List[Dict[str, Any]] = list(orders) if orders else []
        self.active_orders: List[Dict[str, Any]] = []
        self.completed_orders: List[Dict[str, Any]] = []
        self.event_log: List[Dict[str, Any]] = []

        # entidades y reels iniciales
        self.entities: List[Dict[str, Any]] = []
        self.reels: Dict[str, Dict[str, Any]] = {}

        # métricas acumuladas
        self.metrics: Dict[str, Any] = {
            "total_steps": 0,
            "completed_orders": 0,
            "failed_orders": 0,
            "reel_changes": 0,
            "distance_m": 0.0,
            "collisions": 0,
            "downtime_min": 0.0,
            "delivery_times_min": [],
            "utilization_time_min": {},
            "wait_time_min": 0.0,
            "starvations": 0,
        }

        # thread control para modo run()
        self._running = False
        self._lock = threading.RLock()

        # starvation detection helpers
        self._idle_no_orders_min = 0.0
        # starvation flag to detect gaps in supply
        self._starving_flag = False

        # inicializar layout y recursos (subclases pueden extender _init_resources)
        try:
            self._init_layout()
        except Exception:
            # `_init_layout` validará cuando sea apropiado; ignorar si layout parcial
            pass
        try:
            self._init_resources()
        except Exception:
            # permitir que subclases inicialicen más tarde si faltan campos
            pass

    def step(self) -> None:
        """Avanza la simulación un paso de `dt_min` minutos.

        Subclases deben sobreescribir `_update_queue` y `_update_resources`.
        """
        with self._lock:
            self.time_min += self.dt_min
            self.metrics["total_steps"] += 1
            # hooks para subclases
            self._update_queue()
            self._update_resources()
            # Detectar eventos de starvation: cuando no hay órdenes en cola ni activas
            try:
                has_queue = bool(self.queue)
                has_active = bool(self.active_orders)
            except Exception:
                has_queue = bool(self.queue)
                has_active = bool(self.active_orders)
            if not has_queue and not has_active:
                if not getattr(self, "_starving_flag", False):
                    self.metrics["starvations"] = self.metrics.get("starvations", 0) + 1
                    self._starving_flag = True
            else:
                self._starving_flag = False

    def run(self, duration_min: float) -> None:
        """Ejecuta la simulación por `duration_min` minutos en modo síncrono (headless).

        Esto permite tests y ejecuciones batch sin UI.
        """
        self._running = True
        n_steps = int(max(1, round(duration_min / self.dt_min)))
        for _ in range(n_steps):
            if not self._running:
                break
            self.step()

    def stop(self) -> None:
        """Detiene la ejecución iniciada por `run`."""
        self._running = False

    def _update_queue(self) -> None:
        """Basic queue update with lightweight starvation detection.

        In many plant simulations a starvation event is when the system
        (machines/feeds) has no material to process for a sustained period.
        We provide a configurable threshold `starvation_threshold_min` in
        `self.config` (default 2.0 minutes) and increment the
        `metrics['starvations']` counter when the queue remains empty
        beyond the threshold.
        """
        if not self.queue:
            self._idle_no_orders_min += self.dt_min
            threshold = float(self.config.get("starvation_threshold_min", 2.0))
            if self._idle_no_orders_min >= threshold:
                self.metrics["starvations"] = int(self.metrics.get("starvations", 0)) + 1
                # reset to avoid rapid repeated counts
                self._idle_no_orders_min = 0.0
        else:
            self._idle_no_orders_min = 0.0

    def _update_resources(self) -> None:
        """Hook para actualizar entidades y recursos. Subclases lo implementan."""
        return

    def get_snapshot(self) -> Dict[str, Any]:
        """Devuelve un estado minimal serializable para render o tests."""
        return {
            "time_min": self.time_min,
            "dt_min": self.dt_min,
            "entities": [e.copy() for e in self.entities],
            "queue_len": len(self.queue),
            "active_orders": [o.copy() for o in self.active_orders],
            "completed_orders": [o.copy() for o in self.completed_orders],
            "reels": {k: v.copy() for k, v in self.reels.items()},
            "metrics": dict(self.metrics),
        }

    # Compatibilidad con APIs anteriores
    @property
    def orders(self) -> List[Dict[str, Any]]:
        return self.queue

    @orders.setter
    def orders(self, v: List[Dict[str, Any]]):
        self.queue = v

    def _init_layout(self) -> None:
        # validar geometría mínima
        required = ["corrugator", "tracks", "warehouse"]
        for r in required:
            if r not in self.layout:
                raise ValueError(f"Layout missing required element: {r}")

    def _init_resources(self) -> None:
        # inicializar reels desde órdenes
        self._init_layout()
        for o in list(self.queue):
            rid = o.get("reel_id")
            if rid and rid not in self.reels:
                self.reels[rid] = {"status": "in_warehouse", "pos": tuple(self.layout.get("warehouse", {}).get("pos", (0.0, 0.0)))}

    # Helpers de movimiento
    @staticmethod
    def _dist(a: Tuple[float, float], b: Tuple[float, float]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def move_entity_towards(self, entity: Dict[str, Any], target: Tuple[float, float], speed_m_per_min: float) -> None:
        """Mueve la entidad hacia target y contabiliza distancia y utilización.

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
        self.metrics["distance_m"] = self.metrics.get("distance_m", 0.0) + moved
        self.metrics["utilization_time_min"][entity.get("id", "")] = self.metrics["utilization_time_min"].get(entity.get("id", ""), 0.0) + self.step_min

    def calculate_lpi(self) -> float:
        """Calcula el Logistic Pressure Index (0..100) basado en métricas internas.

        Fórmula (ponderada):
          - utilización promedio (0..1) * 0.4
          - saturación de cola (0..1, capped 10) * 0.2
          - starvations (0..1 capped 5) * 0.2
          - distancia relativa (distance_m / 20000) * 0.2
        """
        # evitar división por cero
        time_total = max(self.time_min, 1e-6)
        util_minutes = self.metrics.get("utilization_time_min", {}) or {}
        util_fracs = []
        for t in util_minutes.values():
            try:
                util_fracs.append(float(t) / time_total)
            except Exception:
                continue
        avg_util = float(sum(util_fracs) / len(util_fracs)) if util_fracs else 0.0

        queue_len = len(self.queue)
        starvations = int(self.metrics.get("starvations", 0))
        distance_ratio = float(self.metrics.get("distance_m", 0.0)) / 20000.0

        lpi_frac = (avg_util * 0.4) + (min(queue_len, 10) / 10.0 * 0.2) + (min(starvations, 5) / 5.0 * 0.2) + (distance_ratio * 0.2)
        return min(100.0, max(0.0, lpi_frac * 100.0))

    def get_full_kpis(self) -> Dict[str, Any]:
        """Calcula KPIs a partir de métricas acumuladas.

        Las fórmulas están basadas en métricas reales (tiempos, cuentas, distancias).
        """
        m = self.metrics
        time_total = max(self.time_min, 1e-6)

        reel_changes_per_hour = m.get("reel_changes", 0) / time_total * 60.0

        delivery_times = m.get("delivery_times_min", [])
        avg_delivery = float(statistics.mean(delivery_times)) if delivery_times else 0.0

        completed = int(m.get("completed_orders", 0))
        failed = int(m.get("failed_orders", 0))

        downtime_min = float(m.get("downtime_min", 0.0))
        availability = max(0.0, 1.0 - downtime_min / time_total)

        # Performance: relación entre tiempo nominal y tiempo real.
        nominal_cycle = float(self.config.get("nominal_cycle_min", avg_delivery or 1.0))
        performance = min(1.0, nominal_cycle / avg_delivery) if avg_delivery > 0 else 1.0

        quality = 1.0 - (failed / completed) if completed > 0 else 1.0

        utilization = {}
        for eid, t in m.get("utilization_time_min", {}).items():
            utilization[eid] = (t / time_total) * 100.0

        total_vehicle_hours = sum(m.get("utilization_time_min", {}).values()) / 60.0 if m.get("utilization_time_min") else 0.0
        collisions = m.get("collisions", 0)
        collision_risk_pct = min(100.0, (collisions / max(1.0, total_vehicle_hours)) * 2.0) if total_vehicle_hours > 0 else 0.0

        deliveries_per_min = completed / time_total if time_total > 0 else 0.0
        queue_len = len(self.queue)
        queue_capacity = float(self.config.get("queue_capacity", max(50, queue_len)))
        queue_saturation_pct = min(100.0, (queue_len / queue_capacity) * 100.0) if queue_capacity > 0 else 0.0
        est_wait_time_min = (queue_len / max(1e-6, deliveries_per_min)) if deliveries_per_min > 0 else float("inf")

        return {
            "reel_changes_per_hour": reel_changes_per_hour,
            "avg_delivery_time_min": avg_delivery,
            "starvations": m.get("starvations", 0),
            "downtime_min": downtime_min,
            "oee": availability * performance * quality,
            "availability": availability,
            "performance": performance,
            "quality": quality,
            "utilization_pct": utilization,
            "collision_risk_pct": collision_risk_pct,
            "queue_length": queue_len,
            "queue_saturation_pct": queue_saturation_pct,
            "est_wait_time_min": est_wait_time_min,
            "distance_m": m.get("distance_m", 0.0),
            "collisions": collisions,
            "completed_orders": completed,
            "time_min": time_total,
            "utilization_minutes": m.get("utilization_time_min", {}),
            "total_vehicle_minutes": sum(m.get("utilization_time_min", {}).values()) if m.get("utilization_time_min") else 0.0,
            "lpi": self.calculate_lpi(),
        }

    def inject_event(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> bool:
        """Registrar un evento externo; las subclases pueden ampliar su manejo.

        Devuelve True si el evento fue aplicado.
        """
        self.event_log.append({"time_min": self.time_min, "type": event_type, "payload": payload})
        return False

    @staticmethod
    def _mean(values: List[float]) -> float:
        return float(statistics.mean(values)) if values else 0.0
