from __future__ import annotations

from collections import defaultdict
from .models import EntityBundle


class KnowledgeGraphMemorySystem:
    def __init__(self) -> None:
        self.nodes: dict[str, dict] = {}
        self.edges: dict[str, set[str]] = defaultdict(set)
        self.timeline: dict[str, list[str]] = defaultdict(list)
        self.learned_signals: list[str] = []

    def upsert_entities(self, bundle: EntityBundle) -> None:
        for customer in bundle.customers:
            self.nodes[customer.id] = {"type": "customer", "name": customer.name, "contacts": customer.contacts}

        customer_by_name = {v["name"]: k for k, v in self.nodes.items() if v.get("type") == "customer"}

        for offer in bundle.offers:
            self.nodes[offer.id] = {"type": "offer", "client": offer.client, "price": offer.price, "description": offer.description}
            c_id = customer_by_name.get(offer.client)
            if c_id:
                self.edges[c_id].add(offer.id)
                self.timeline[offer.client].append(f"offer:{offer.id}:{offer.date or 'unknown'}")

        for sale in bundle.sales:
            self.nodes[sale.id] = {"type": "sale", "client": sale.client, "value": sale.value, "product": sale.product}
            c_id = customer_by_name.get(sale.client)
            if c_id:
                self.edges[c_id].add(sale.id)
                self.timeline[sale.client].append(f"sale:{sale.id}:{sale.date or 'unknown'}")

        for opp in bundle.opportunities:
            self.nodes[opp.id] = {
                "type": "opportunity",
                "client": opp.client,
                "amount": opp.amount,
                "description": opp.description,
                "close_date": opp.close_date,
            }
            c_id = customer_by_name.get(opp.client)
            if c_id:
                self.edges[c_id].add(opp.id)
                self.timeline[opp.client].append(f"opportunity:{opp.id}:{opp.close_date or 'unknown'}")

    def semantic_search(self, query: str) -> list[dict]:
        q = query.lower()
        return [
            {"id": node_id, **data}
            for node_id, data in self.nodes.items()
            if q in str(data).lower()
        ]

    def feed_learning(self, signal: str) -> None:
        if signal and signal not in self.learned_signals:
            self.learned_signals.append(signal)
