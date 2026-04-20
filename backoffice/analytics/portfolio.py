"""Product portfolio analysis — lifecycle classification."""
from __future__ import annotations
from collections import defaultdict
from typing import Any, Dict, List

from backoffice.graph.store import GraphStore


class PortfolioAnalyzer:
    """Classifies products by lifecycle stage based on sales velocity."""

    def __init__(self, store: GraphStore):
        self._store = store

    def _product_sales_volume(self) -> Dict[str, float]:
        volume: Dict[str, float] = defaultdict(float)
        for sale in self._store.get_all_sales():
            for pid in sale.product_ids:
                volume[pid] += sale.amount_eur or sale.amount
        return dict(volume)

    def classify_products(self) -> List[Dict[str, Any]]:
        volume = self._product_sales_volume()
        products = self._store.get_all_products()
        if not products:
            return []

        total_volume = sum(volume.values()) or 1.0
        results = []
        for product in products:
            rev = volume.get(product.id, 0.0)
            share = rev / total_volume

            if product.lifecycle_stage != "active":
                stage = product.lifecycle_stage
            elif share >= 0.30:
                stage = "commodity"
            elif share >= 0.10:
                stage = "growth"
            elif share > 0:
                stage = "decline"
            else:
                stage = "innovation"

            results.append({
                "product_id": product.id,
                "name": product.name,
                "lifecycle_stage": stage,
                "revenue_share": round(share, 4),
                "total_revenue_eur": round(rev, 2),
            })
        results.sort(key=lambda x: x["revenue_share"], reverse=True)
        return results
