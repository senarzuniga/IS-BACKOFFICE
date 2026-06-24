"""Generador de órdenes realistas para el simulador de bobinas.
"""
from typing import List, Dict, Optional, Tuple
import random


PAPER_TYPES = [
    ("Kraft 125", 125),
    ("Kraft 150", 150),
    ("Kraft 200", 200),
    ("Testliner 125", 125),
    ("White Top 140", 140),
    ("Recycled Liner 135", 135),
]


def generate_orders(n: int, seed: Optional[int] = None, dist: Tuple[float, float, float] = (0.2, 0.5, 0.3), tracks: Optional[List[str]] = None) -> List[Dict[str, any]]:
    """Genera `n` órdenes con distribución short/medium/long.

    - dist: probabilidades para (short, medium, long)
    - tracks: lista de track ids posibles (ej: ['RS1_A','RS2_B'])
    """
    if seed is not None:
        random.seed(seed)
    # Defensive: allow callers to pass dist=None explicitly and fall back
    # to the library default distribution.
    if dist is None:
        dist = (0.2, 0.5, 0.3)
    orders = []
    for i in range(n):
        r = random.random()
        if r < dist[0]:
            meters = random.randint(300, 1000)
            length_type = "short"
        elif r < dist[0] + dist[1]:
            meters = random.randint(1001, 3000)
            length_type = "medium"
        else:
            meters = random.randint(3001, 8000)
            length_type = "long"

        paper, gsm = random.choice(PAPER_TYPES)
        priority_r = random.random()
        if priority_r < 0.2:
            priority = "high"
        elif priority_r < 0.7:
            priority = "medium"
        else:
            priority = "low"

        track_id = (random.choice(tracks) if tracks else "RS3_A")

        order = {
            "reel_id": f"R{i+1}",
            "paper_type": paper,
            "gsm": gsm,
            "meters": meters,
            "length_type": length_type,
            "priority": priority,
            "track_id": track_id,
            "deadline_min": random.randint(60, 300),
            # timestamp when the order was created (simulation minutes)
            "created_time_min": 0.0,
        }
        orders.append(order)
    return orders
