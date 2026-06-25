"""
Factores humanos que afectan al escenario FORKLIFT.

Incluye búsqueda de bobina, retrasos por tráfico, pausas/turnos y errores humanos.
"""
import random
from typing import Dict


class HumanFactors:
    def __init__(self, config: Dict, rng: random.Random):
        self.rng = rng
        self.shift_interval = config.get("shift_interval_min", 240)  # 4h
        self.shift_duration = config.get("shift_duration_min", 5)
        self.operator_break_interval = config.get("operator_break_interval_min", 120)  # 2h
        self.operator_break_duration = config.get("operator_break_duration_min", 15)
        self.reel_search_prob = config.get("reel_search_prob", 0.10)
        self.traffic_prob = config.get("traffic_prob", 0.20)
        self.error_prob = config.get("error_prob", 0.02)
        self.conflict_prob = config.get("conflict_prob", 0.05)

    def get_search_time(self) -> float:
        """Tiempo de búsqueda de bobina en almacén (15-90s) en minutos."""
        if self.rng.random() < self.reel_search_prob:
            return self.rng.uniform(15.0 / 60.0, 90.0 / 60.0)
        return 0.0

    def get_traffic_delay(self) -> float:
        """Retraso por tráfico/cruces (5-30s) en minutos."""
        if self.rng.random() < self.traffic_prob:
            return self.rng.uniform(5.0 / 60.0, 30.0 / 60.0)
        return 0.0

    def has_error(self) -> bool:
        return self.rng.random() < self.error_prob

    def has_conflict(self) -> bool:
        return self.rng.random() < self.conflict_prob

    def get_shift_status(self, time_min: float) -> Dict:
        shift_number = int(time_min / self.shift_interval)
        time_in_shift = time_min % self.shift_interval

        is_shift_change = time_in_shift < self.shift_duration
        is_operator_break = (
            (time_in_shift % self.operator_break_interval) < self.operator_break_duration
            and time_in_shift > self.shift_duration
        )

        return {
            "shift_number": shift_number,
            "is_shift_change": is_shift_change,
            "is_operator_break": is_operator_break,
            "is_active": not is_shift_change and not is_operator_break,
        }
