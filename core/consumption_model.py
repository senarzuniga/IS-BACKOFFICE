"""
Modelo de consumo continuo de papel en la corrugadora.

Este módulo implementa la conversión entre peso de bobina (kg) y
metros producibles, la velocidad de la corrugadora y reglas de
umbral para considerar una bobina "agotada" o parcial.
"""
from typing import Dict


class ConsumptionModel:
    def __init__(self, config: Dict = None):
        config = config or {}
        self.corrugator_speed_m_min = float(config.get("corrugator_speed_m_min", 250.0))
        self.reel_weight_kg = float(config.get("default_reel_weight_kg", 1000.0))
        self.reel_width_m = float(config.get("reel_width_m", 2.5))
        # paper weight in kg per m^2 (e.g. 0.15 kg/m2 == 150 g/m2)
        self.paper_weight_kg_m2 = float(config.get("paper_weight_kg_m2", 0.15))
        # threshold under which a reel is considered "partial/returned" (default 30%)
        self.min_reel_weight_kg = float(config.get("min_reel_weight_kg", self.reel_weight_kg * 0.3))

    def calculate_consumption(self, time_min: float) -> float:
        """Calcula los metros producidos en un intervalo de tiempo (minutos)."""
        return float(self.corrugator_speed_m_min) * float(time_min)

    def calculate_reel_life(self, reel_weight: float) -> float:
        """Calcula el tiempo de vida de una bobina (en minutos).

        metros producibles = (peso / (ancho * gramaje))
        tiempo (min) = metros / velocidad
        """
        if reel_weight <= 0:
            return 0.0
        meters = (float(reel_weight) / (self.reel_width_m * self.paper_weight_kg_m2))
        return meters / max(1e-9, self.corrugator_speed_m_min)

    def is_reel_depleted(self, current_reel_weight: float) -> bool:
        """Determina si una bobina está por debajo del umbral de utilidad."""
        return float(current_reel_weight) < float(self.min_reel_weight_kg)

    def calculate_remaining_meters(self, reel_weight: float) -> float:
        """Calcula los metros restantes de una bobina dado su peso (kg)."""
        if reel_weight <= 0:
            return 0.0
        return float(reel_weight) / (self.reel_width_m * self.paper_weight_kg_m2)

    def kg_per_meter(self) -> float:
        """Devuelve los kg consumidos por metro producido."""
        return float(self.paper_weight_kg_m2 * self.reel_width_m)
