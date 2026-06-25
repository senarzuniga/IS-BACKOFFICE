"""
Starvation detector: registra eventos cuando la corrugadora se queda sin bobina
disponible para continuar la producción.
"""


class StarvationDetector:
    def __init__(self):
        self.starvation_events = 0
        self.starvation_time = 0.0
        self.is_starving = False

    def check_starvation(self, current_reel_weight: float, time_step: float) -> bool:
        """Verifica si la corrugadora entra en starvation.

        Criterio simple: si el peso actual cae por debajo del umbral de 30%.
        """
        threshold = 150.0  # kg (asumido 30% de 1000kg por defecto)
        if current_reel_weight < threshold:
            if not self.is_starving:
                self.is_starving = True
                self.starvation_events += 1
            self.starvation_time += time_step
            return True
        else:
            self.is_starving = False
            return False

    def get_starvation_metrics(self) -> dict:
        return {"events": self.starvation_events, "total_time_min": self.starvation_time}
