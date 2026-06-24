"""Motor de simulación para escenario Forklift (carretillas).
"""
from typing import Dict, Any, List, Tuple
import random

from .base_simulation_engine import BaseSimulationEngine


class ForkliftSimulationEngine(BaseSimulationEngine):
    """Simulación basada en carretillas.

    Config esperado en self.config:
    - n_forklifts: int
    - forklift_speed_loaded: m/min
    - forklift_speed_empty: m/min
    - buffer_capacity: int
    """

    def _init_resources(self):
        super()._init_resources()
        n = int(self.config.get("n_forklifts", 2))
        self.entities = []
        for i in range(n):
            ent = {
                "id": f"forklift_{i+1}",
                "type": "forklift",
                "pos": tuple(self.layout["warehouse"]["pos"]),
                "state": "idle",
                "task": None,
            }
            self.entities.append(ent)
            self.metrics["utilization_time_min"][ent["id"]] = 0.0

        # Buffer
        self.buffer_slots = []
        cap = int(self.config.get("buffer_capacity", 8))
        # buffer positions simple grid within buffer_zone
        if "buffer_zone" in self.layout:
            bx, by = self.layout["buffer_zone"]["pos"]
            bw, bh = self.layout["buffer_zone"]["size"]
            for r in range(cap):
                sx = bx + (r % 4) * 3.0
                sy = by + (r // 4) * 3.0
                self.buffer_slots.append({"pos": (sx, sy), "occupied": False})

    def step(self):
        # Reglas simples por paso
        super().step()
        # Asignar tareas si hay órdenes
        for e in self.entities:
            if e["state"] == "idle":
                # tomar una orden si existe
                if self.orders:
                    order = self.orders.pop(0)
                    # mark when this order started processing
                    order["start_time_min"] = self.time_min
                    e["task"] = order
                    e["state"] = "to_warehouse"
                else:
                    e["state"] = "idle"

            if e["state"] == "to_warehouse":
                # ir a warehouse para cargar
                target = tuple(self.layout["warehouse"]["pos"])
                speed = self.config.get("forklift_speed_empty", 80.0)
                self.move_entity_towards(e, target, speed)
                if tuple(e["pos"]) == target:
                    # cargar bobina si hay
                    reel = e["task"].get("reel_id")
                    if reel and self.reels.get(reel):
                        self.reels[reel]["status"] = "on_forklift"
                        e["state"] = "to_buffer"

            elif e["state"] == "to_buffer":
                # ir a buffer y soltar
                # elegir slot libre
                free = next((s for s in self.buffer_slots if not s["occupied"]), None)
                if free:
                    target = free["pos"]
                    speed = self.config.get("forklift_speed_loaded", 60.0)
                    self.move_entity_towards(e, target, speed)
                    if tuple(e["pos"]) == target:
                        free["occupied"] = True
                        reel = e["task"].get("reel_id")
                        if reel:
                            self.reels[reel]["status"] = "in_buffer"
                            self.reels[reel]["pos"] = target
                            self.metrics["reel_changes"] += 1
                        e["state"] = "to_track"
                else:
                    # buffer full -> esperar
                    e["state"] = "waiting_buffer"
                    self.metrics["wait_time_min"] += self.step_min

            elif e["state"] == "waiting_buffer":
                # intentar de nuevo aleatoriamente
                if random.random() < 0.3:
                    e["state"] = "to_buffer"

            elif e["state"] == "to_track":
                # llevar bobina del buffer al track destino
                track_id = e["task"].get("track_id")
                if track_id and track_id in self.layout.get("tracks", {}):
                    tx, ty = tuple(self.layout["tracks"][track_id]["pos"])
                    # aproximarse al frente del track
                    speed = self.config.get("forklift_speed_loaded", 60.0)
                    self.move_entity_towards(e, (tx, ty - 2.0), speed)
                    if abs(e["pos"][0] - tx) < 0.5:
                        # soltar
                        reel = e["task"].get("reel_id")
                        if reel:
                            self.reels[reel]["status"] = "on_track"
                            self.reels[reel]["pos"] = (tx, ty)
                            self.metrics["reel_changes"] += 1
                            # mark completion
                            try:
                                start = e["task"].get("start_time_min", e["task"].get("created_time_min", 0.0))
                                dt = max(0.0, self.time_min - float(start))
                                self.metrics.setdefault("delivery_times_min", []).append(dt)
                            except Exception:
                                pass
                            self.metrics["completed_orders"] = int(self.metrics.get("completed_orders", 0)) + 1
                        # finish task and return
                        e["task"] = None
                        e["state"] = "returning"
                else:
                    # track no encontrado
                    e["state"] = "idle"

            elif e["state"] == "returning":
                # volver a almacén
                target = tuple(self.layout["warehouse"]["pos"])
                speed = self.config.get("forklift_speed_empty", 80.0)
                self.move_entity_towards(e, target, speed)
                if tuple(e["pos"]) == target:
                    e["state"] = "idle"
                    e["task"] = None

        # Detección simple de colisiones (prox < 0.5 m)
        for i in range(len(self.entities)):
            for j in range(i + 1, len(self.entities)):
                if self._dist(tuple(self.entities[i]["pos"]), tuple(self.entities[j]["pos"])) < 0.5:
                    self.metrics["collisions"] += 1

    def inject_event(self, event_type: str, payload: Dict[str, Any] = None):
        # manejar eventos simples
        if event_type == "forklift_blocked":
            # bloquear una carretilla aleatoria
            if self.entities:
                ent = random.choice(self.entities)
                ent["state"] = "blocked"
                return True
        return False
