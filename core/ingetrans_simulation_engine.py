"""Motor de simulación para escenario INGETRANS (transfer sobre rail).
"""
from typing import Dict, Any, List, Tuple

from .base_simulation_engine import BaseSimulationEngine


class IngetransSimulationEngine(BaseSimulationEngine):
    """Simulación basada en un transfer que se mueve en un rail longitudinal.

    Config esperado:
    - transfer_speed: m/min
    - pick_up_s: segundos
    - drop_off_s: segundos
    - capacity: int (número de bobinas)
    """

    def _init_resources(self):
        super()._init_resources()
        # crear una única entidad transfer
        home = tuple(self.layout.get("ingetrans_home", (30.0, 20.0)))
        ent = {
            "id": "transfer_1",
            "type": "transfer",
            "pos": home,
            "state": "idle",
            "task": None,
            "loaded": [],
        }
        self.entities = [ent]
        self.metrics["utilization_time_min"][ent["id"]] = 0.0

    def step(self):
        super().step()
        ent = self.entities[0]
        # Comportamiento simple de pick/delivery
        if ent["state"] == "idle":
            # tomar orden si existe
            if self.orders:
                order = self.orders.pop(0)
                ent["task"] = order
                ent["state"] = "to_exchange"

        elif ent["state"] == "to_exchange":
            target = tuple(self.layout.get("exchange_zone", {}).get("pos", (24.0, 14.0)))
            speed = self.config.get("transfer_speed", 80.0)
            self.move_entity_towards(ent, target, speed)
            if self._dist(tuple(ent["pos"]), target) < 0.5:
                ent["state"] = "pickup"
                ent["pickup_timer"] = self.config.get("pick_up_s", 6) / 60.0  # convertir a minutos

        elif ent["state"] == "pickup":
            ent["pickup_timer"] -= self.step_min
            if ent["pickup_timer"] <= 0:
                # cargar si hay reel en warehouse o exchange
                reel = ent["task"].get("reel_id")
                if reel and self.reels.get(reel):
                    self.reels[reel]["status"] = "on_transfer"
                    ent["loaded"].append(reel)
                ent["state"] = "to_track"

        elif ent["state"] == "to_track":
            track_id = ent["task"].get("track_id")
            tx, ty = tuple(self.layout["tracks"][track_id]["pos"])
            # moverse sólo en X sobre el rail
            target = (tx, ent["pos"][1])
            speed = self.config.get("transfer_speed", 80.0)
            self.move_entity_towards(ent, target, speed)
            if abs(ent["pos"][0] - tx) < 0.5:
                ent["state"] = "dropoff"
                ent["dropoff_timer"] = self.config.get("drop_off_s", 6) / 60.0

        elif ent["state"] == "dropoff":
            ent["dropoff_timer"] -= self.step_min
            if ent["dropoff_timer"] <= 0:
                # soltar en track
                for reel in ent["loaded"]:
                    self.reels[reel]["status"] = "on_track"
                    self.reels[reel]["pos"] = tuple(self.layout["tracks"][ent["task"]["track_id"]]["pos"])
                    self.metrics["reel_changes"] += 1
                ent["loaded"] = []
                ent["state"] = "return_home"

        elif ent["state"] == "return_home":
            home = tuple(self.layout.get("ingetrans_home", (30.0, 20.0)))
            speed = self.config.get("transfer_speed", 80.0)
            self.move_entity_towards(ent, home, speed)
            if self._dist(tuple(ent["pos"]), home) < 0.2:
                ent["state"] = "idle"
                ent["task"] = None

    def inject_event(self, event_type: str, payload: Dict[str, Any] = None):
        if event_type == "transfer_delay":
            # simular retraso en pickup o dropoff
            ent = self.entities[0]
            if ent["state"] in ("pickup", "dropoff"):
                extra = payload.get("extra_s", 10) / 60.0 if payload else 10 / 60.0
                ent_key = "pickup_timer" if ent["state"] == "pickup" else "dropoff_timer"
                ent[ent_key] = ent.get(ent_key, 0.0) + extra
                return True
        return False
