"""In-memory knowledge graph store."""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Type, TypeVar

from backoffice.models.base import BaseEntity
from backoffice.models.client import Client
from backoffice.models.contact import Contact
from backoffice.models.offer import Offer
from backoffice.models.opportunity import Opportunity
from backoffice.models.sale import Sale
from backoffice.models.product import Product
from backoffice.models.document import Document
from .relations import Relation, RelationType

T = TypeVar("T", bound=BaseEntity)


class GraphStore:
    """Persistent in-memory store for all entities and relationships."""

    def __init__(self):
        self._clients: Dict[str, Client] = {}
        self._contacts: Dict[str, Contact] = {}
        self._offers: Dict[str, Offer] = {}
        self._opportunities: Dict[str, Opportunity] = {}
        self._sales: Dict[str, Sale] = {}
        self._products: Dict[str, Product] = {}
        self._documents: Dict[str, Document] = {}
        self._relations: List[Relation] = []

    # ── Generic helpers ───────────────────────────────────────────────────────

    def _store_map(self, entity_type: str) -> Dict:
        return {
            "client": self._clients,
            "contact": self._contacts,
            "offer": self._offers,
            "opportunity": self._opportunities,
            "sale": self._sales,
            "product": self._products,
            "document": self._documents,
        }[entity_type]

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def upsert_client(self, client: Client) -> Client:
        self._clients[client.id] = client
        return client

    def upsert_contact(self, contact: Contact) -> Contact:
        self._contacts[contact.id] = contact
        return contact

    def upsert_offer(self, offer: Offer) -> Offer:
        self._offers[offer.id] = offer
        return offer

    def upsert_opportunity(self, opp: Opportunity) -> Opportunity:
        self._opportunities[opp.id] = opp
        return opp

    def upsert_sale(self, sale: Sale) -> Sale:
        self._sales[sale.id] = sale
        return sale

    def upsert_product(self, product: Product) -> Product:
        self._products[product.id] = product
        return product

    def upsert_document(self, doc: Document) -> Document:
        self._documents[doc.id] = doc
        return doc

    def add_relation(self, relation: Relation) -> Relation:
        self._relations.append(relation)
        return relation

    # ── Queries ───────────────────────────────────────────────────────────────

    def get_client(self, client_id: str) -> Optional[Client]:
        return self._clients.get(client_id)

    def get_all_clients(self) -> List[Client]:
        return list(self._clients.values())

    def get_all_offers(self) -> List[Offer]:
        return list(self._offers.values())

    def get_all_sales(self) -> List[Sale]:
        return list(self._sales.values())

    def get_all_opportunities(self) -> List[Opportunity]:
        return list(self._opportunities.values())

    def get_all_products(self) -> List[Product]:
        return list(self._products.values())

    def get_relations_for(self, entity_id: str,
                           rel_type: Optional[RelationType] = None) -> List[Relation]:
        result = [r for r in self._relations
                  if r.source_id == entity_id or r.target_id == entity_id]
        if rel_type:
            result = [r for r in result if r.relation_type == rel_type]
        return result

    def get_client_timeline(self, client_id: str) -> Dict[str, Any]:
        """Return a full timeline of client activity."""
        offers = [o for o in self._offers.values() if o.client_id == client_id]
        sales = [s for s in self._sales.values() if s.client_id == client_id]
        opps = [o for o in self._opportunities.values() if o.client_id == client_id]
        contacts = [c for c in self._contacts.values() if c.client_id == client_id]
        return {
            "client_id": client_id,
            "offers": [o.model_dump() for o in sorted(offers, key=lambda x: x.created_at)],
            "sales": [s.model_dump() for s in sorted(sales, key=lambda x: x.created_at)],
            "opportunities": [o.model_dump() for o in sorted(opps, key=lambda x: x.created_at)],
            "contacts": [c.model_dump() for c in contacts],
        }

    def stats(self) -> Dict[str, int]:
        return {
            "clients": len(self._clients),
            "contacts": len(self._contacts),
            "offers": len(self._offers),
            "opportunities": len(self._opportunities),
            "sales": len(self._sales),
            "products": len(self._products),
            "documents": len(self._documents),
            "relations": len(self._relations),
        }
