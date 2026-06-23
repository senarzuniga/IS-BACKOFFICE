"""Work Order Agent — genera órdenes de fabricación para la simulación."""
from __future__ import annotations

import random
from typing import List, Dict, Any


class WorkOrderAgent:
    """Genera órdenes de forma aleatoria o carga desde CSV/Excel (próximamente).

    Cada orden contiene: id, paper_type, meters_to_produce
    """

    PAPER_TYPES = ["Kraft 125", "Kraft 150", "Kraft 200", "Testliner 125", "White Top"]

    def generate_orders(self, n: int = 8) -> List[Dict[str, Any]]:
        orders = []
        for i in range(n):
            orders.append({
                "id": f"WO-{random.randint(1000,9999)}",
                "paper_type": random.choice(self.PAPER_TYPES),
                "meters": random.randint(300, 7000),
            })
        return orders
