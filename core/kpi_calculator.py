from typing import Dict


def calculate_kpis(engine) -> Dict[str, float]:
    """Compute KPIs (Track Saturation, RRI, PSS, LPI, OEE) from the engine.

    Returns values scaled to intuitive ranges (percentages for many KPIs).
    """
    num_tracks = max(len(engine.tracks), 1)
    occupied = sum(1 for t in engine.tracks if t["state"].name != "EMPTY")
    track_saturation = (occupied / num_tracks) * 100.0

    # RRI: readiness index, scale average remaining fraction to a number >0
    avg_remaining = sum(s.remaining_fraction() for s in engine.roll_stands) / max(len(engine.roll_stands), 1)
    rri = avg_remaining * 1.5  # dimensionless, typical target around 1.0-1.5

    # PSS: predictive supply score (percent deliveries on-time for INGETRANS)
    scheduled = max(engine.metrics.get("deliveries_scheduled", 0), 0)
    successful = max(engine.metrics.get("deliveries_successful", 0), 0)
    pss = 100.0 if scheduled == 0 else (successful / scheduled) * 100.0

    # LPI: logistic pressure index, combine saturation and pending deliveries
    pending = engine.pending_deliveries_count()
    pending_ratio = pending / max(num_tracks, 1)
    lpi = min(100.0, track_saturation * 0.6 + pending_ratio * 100.0 * 0.4)

    # OEE: simple production-based OEE (production vs theoretical)
    theoretical = engine.theoretical_max_production()
    produced = max(engine.metrics.get("production_meters", 0.0), 0.0)
    oee = (produced / theoretical) * 100.0 if theoretical > 0 else 0.0

    # Boundaries
    rri = float(rri)
    pss = max(0.0, min(100.0, float(pss)))
    lpi = max(0.0, min(100.0, float(lpi)))
    oee = max(0.0, min(100.0, float(oee)))

    return {
        "track_saturation": track_saturation,
        "RRI": rri,
        "PSS": pss,
        "LPI": lpi,
        "OEE": oee,
    }
