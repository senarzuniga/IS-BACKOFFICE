from dataclasses import dataclass
from typing import List


@dataclass
class Layer:
    name: str
    remaining_m: float


class RollStand:
    """Represents a roll stand that consumes 5 layers simultaneously.

    Layers: Liner1, Liner2, Medium, Liner3, Liner4
    Consumption is modelled in meters per minute (corrugator speed).
    """

    LAYER_NAMES = ["Liner1", "Liner2", "Medium", "Liner3", "Liner4"]

    def __init__(self, stand_id: int, avg_reel_length_m: float, corrugator_speed_m_per_min: float):
        self.id = stand_id
        self.corrugator_speed = corrugator_speed_m_per_min
        self.initial_reel_length = float(avg_reel_length_m)
        self.layers: List[Layer] = [Layer(n, float(avg_reel_length_m)) for n in self.LAYER_NAMES]
        self.active = True

    def consume(self, dt_min: float) -> float:
        """Consume material from each layer for dt_min minutes.

        Returns total meters produced by this stand (one output meter per minute).
        """
        # The actual produced meters is limited by the layer that has the least available
        amount = self.corrugator_speed * dt_min
        consumed_per_layer = [min(layer.remaining_m, amount) for layer in self.layers]
        # production possible is limited by the minimum consumed across layers
        produced = min(consumed_per_layer) if consumed_per_layer else 0.0
        # subtract produced amount from each layer (simultaneous consumption)
        for layer in self.layers:
            layer.remaining_m -= produced
        return produced

    def needs_reel(self, threshold_fraction: float = 0.1) -> bool:
        """Return True if any layer has remaining fraction less than threshold_fraction."""
        for layer in self.layers:
            if layer.remaining_m / max(self.initial_reel_length, 1.0) <= threshold_fraction:
                return True
        return False

    def remaining_fraction(self) -> float:
        """Average remaining fraction across all layers."""
        total = sum(max(layer.remaining_m, 0.0) for layer in self.layers)
        return total / (len(self.layers) * max(self.initial_reel_length, 1.0))

    def install_new_reel(self, length_m: float = None):
        """Install a new reel (reset remaining meters on each layer)."""
        length = float(length_m) if length_m is not None else float(self.initial_reel_length)
        for layer in self.layers:
            layer.remaining_m = length
        self.initial_reel_length = length
