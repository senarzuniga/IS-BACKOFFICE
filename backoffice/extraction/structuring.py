from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass
class Customer:
    id: str
    name: str
    contacts: list[str] = field(default_factory=list)


@dataclass
class Opportunity:
    id: str
    client: str
    description: str
    amount: float
    close_date: str | None


@dataclass
class Offer:
    id: str
    client: str
    description: str
    price: float
    date: str | None


@dataclass
class Sale:
    id: str
    client: str
    product: str
    value: float
    date: str | None


@dataclass
class EntityBundle:
    customers: list[Customer]
    opportunities: list[Opportunity]
    offers: list[Offer]
    sales: list[Sale]


class EntityExtractionStructuringEngine:
    def extract(self, records: list) -> EntityBundle:
        customers: dict[str, Customer] = {}
        opportunities: list[Opportunity] = []
        offers: list[Offer] = []
        sales: list[Sale] = []

        for record in records:
            pairs = self._parse_pairs(record.content)
            client = pairs.get("client") or record.client_reference or "unknown"
            customer = customers.setdefault(client, Customer(id=make_id("customer"), name=client))
            if "contact" in pairs and pairs["contact"] not in customer.contacts:
                customer.contacts.append(pairs["contact"])

            if "offer" in pairs or record.classification == "offer":
                offers.append(
                    Offer(
                        id=make_id("offer"),
                        client=client,
                        description=pairs.get("offer", "offer"),
                        price=self._as_float(pairs.get("price", "0")),
                        date=pairs.get("date"),
                    )
                )

            if "sale" in pairs or record.classification == "sale":
                sales.append(
                    Sale(
                        id=make_id("sale"),
                        client=client,
                        product=pairs.get("product", pairs.get("sale", "service")),
                        value=self._as_float(pairs.get("value", pairs.get("price", "0"))),
                        date=pairs.get("date"),
                    )
                )

            if "opportunity" in pairs:
                opportunities.append(
                    Opportunity(
                        id=make_id("opportunity"),
                        client=client,
                        description=pairs["opportunity"],
                        amount=self._as_float(pairs.get("value", pairs.get("price", "0"))),
                        close_date=pairs.get("deadline", pairs.get("date")),
                    )
                )

        return EntityBundle(customers=list(customers.values()), opportunities=opportunities, offers=offers, sales=sales)

    @staticmethod
    def _parse_pairs(text: str) -> dict[str, str]:
        parsed: dict[str, str] = {}
        if not text:
            return parsed

        matches = list(re.finditer(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*=", text))
        if not matches:
            return parsed

        for idx, match in enumerate(matches):
            key = match.group(1).strip().lower()
            value_start = match.end()
            value_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            value = text[value_start:value_end].strip(" ;,\t\n\r")
            if value:
                parsed[key] = value
        return parsed

    @staticmethod
    def _as_float(value: str) -> float:
        cleaned = value.replace("USD", "").replace("EUR", "").replace("$", "").replace("€", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
