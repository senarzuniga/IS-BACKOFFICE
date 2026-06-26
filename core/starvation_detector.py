"""
Starvation detector: registra eventos cuando la corrugadora se queda sin bobina
disponible para continuar la producción.
"""


class StarvationDetector:
    def __init__(self, threshold_kg: float = 150.0):
        """
        threshold_kg: peso (kg) bajo el cual la bobina se considera insuficiente
                      y se inicia un evento de starvation.
        """
        self.threshold_kg = float(threshold_kg)
        self.starvation_events = 0
        self.starvation_time = 0.0
        self.is_starving = False

    def check_starvation(self, current_reel_weight: float, time_step: float) -> bool:
        """Verifica si la corrugadora entra en starvation.

        Usa el umbral configurado en el detector (`threshold_kg`).
        """
        if float(current_reel_weight) < self.threshold_kg:
            if not self.is_starving:
                self.is_starving = True
                self.starvation_events += 1
            self.starvation_time += float(time_step)
            return True
        else:
            self.is_starving = False
            return False

    def get_starvation_metrics(self) -> dict:
        return {"events": self.starvation_events, "total_time_min": self.starvation_time, "threshold_kg": self.threshold_kg}
