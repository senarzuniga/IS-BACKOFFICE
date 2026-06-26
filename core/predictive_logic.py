import random
from typing import Optional


def should_pre_reserve(stand, config) -> bool:
    """Decide whether to pre-reserve a track for INGETRANS based on time-to-depletion.

    Returns True if we should pre-reserve now.
    """
    lead_time = float(config.get("ingetrans_predictive_lead_time_min", 10.0))
    # compute time to depletion in minutes
    remaining_m = stand.layers[0].remaining_m if stand.layers else 0.0
    # approximate remaining using average across layers
    total_remaining = sum(layer.remaining_m for layer in stand.layers)
    avg_remaining = total_remaining / max(len(stand.layers), 1)
    time_to_depletion = avg_remaining / max(stand.corrugator_speed, 0.0001)
    return time_to_depletion <= lead_time


def predict_arrival_time(current_time: float, config, rng: random.Random) -> float:
    """Return an arrival delay (minutes) for INGETRANS transfers.

    Keep arrival fast and deterministic compared to forklift.
    """
    base = float(config.get("transfer_pickup_reel", 6.0)) + float(config.get("transfer_dropoff_reel", 6.0))
    overhead = float(config.get("transfer_start_stop_overhead", 9.0))
    travel = float(config.get("exchange_to_track_load", 9.0)) / max(float(config.get("transfer_max_speed", 80.0)), 1.0) * 60.0
    # Add small jitter
    jitter = rng.normalvariate(0, 0.1)
    return current_time + max(0.5, (base + overhead + travel) / 60.0 + jitter)
