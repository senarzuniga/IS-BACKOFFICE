"""Gestor simple de eventos inyectables para el simulador.
"""
from typing import Dict, Any


class EventManager:
    """Registro e inyección de eventos en engines."""

    def __init__(self):
        self.log = []

    def inject(self, engine, event_type: str, payload: Dict[str, Any] = None) -> bool:
        entry = {"time_min": getattr(engine, "time_min", 0.0), "type": event_type, "payload": payload}
        self.log.append(entry)
        try:
            applied = engine.inject_event(event_type, payload)
            return bool(applied)
        except Exception:
            return False
