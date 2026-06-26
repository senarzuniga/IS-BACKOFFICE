import random
from typing import Optional


def reactive_arrival_time(current_time: float, config, rng: random.Random) -> float:
    """Return an arrival time (minutes absolute) for Forklift deliveries.

    Forklift is slower and has more variability.
    """
    # times in seconds configured in config
    pickup = float(config.get("forklift_pickup_time", 30.0))
    dropoff = float(config.get("forklift_dropoff_time", 20.0))
    search = float(config.get("avg_search_time", 25.0))
    maneuver = float(config.get("avg_maneuver_time", 15.0))
    travel_m = float(config.get("transfer_travel_length", 50.0))
    loaded_speed = float(config.get("forklift_loaded_speed", 60.0))
    # convert speeds to m/s for travel time
    loaded_speed_m_per_s = max(loaded_speed / 60.0, 0.1)
    travel_time_s = travel_m / loaded_speed_m_per_s
    base_seconds = pickup + dropoff + search + maneuver + travel_time_s
    # variability
    jitter = rng.uniform(0.8, 1.4)
    total_seconds = base_seconds * jitter
    # add a small extra delay to reflect searching/coordination overhead
    extra = float(config.get("forklift_extra_delay_s", 60.0))
    total_seconds += extra
    return current_time + max(0.1, total_seconds / 60.0)
