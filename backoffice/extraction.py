from __future__ import annotations

from .models import Customer, EntityBundle, Offer, Opportunity, RawRecord, Sale, make_id


class EntityExtractionStructuringEngine:
    def extract(self, records: list[RawRecord]) -> EntityBundle:
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
        for part in text.split(";"):
            if "=" not in part:
                continue
            k, v = part.split("=", 1)
            parsed[k.strip().lower()] = v.strip()
        return parsed

    @staticmethod
    def _as_float(value: str) -> float:
        cleaned = value.replace("USD", "").replace("EUR", "").replace("$", "").replace("€", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
