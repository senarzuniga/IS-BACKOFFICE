"""Graph & knowledge API routes."""
from fastapi import APIRouter, HTTPException
from backoffice.graph.search import SemanticSearch
from backoffice.models.client import Client
from backoffice.models.offer import Offer
from backoffice.models.sale import Sale
from backoffice.models.opportunity import Opportunity
from backoffice.models.product import Product
from api.state import graph_store

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/stats")
def get_stats():
    return graph_store.stats()


@router.get("/search")
def search(q: str, top_k: int = 10):
    searcher = SemanticSearch(graph_store)
    return {"query": q, "results": searcher.search(q, top_k=top_k)}


@router.get("/clients")
def list_clients():
    return [c.model_dump() for c in graph_store.get_all_clients()]


@router.get("/clients/{client_id}/timeline")
def client_timeline(client_id: str):
    timeline = graph_store.get_client_timeline(client_id)
    if not timeline:
        raise HTTPException(status_code=404, detail="Client not found")
    return timeline


@router.post("/clients")
def create_client(client: Client):
    graph_store.upsert_client(client)
    return client.model_dump()


@router.post("/offers")
def create_offer(offer: Offer):
    graph_store.upsert_offer(offer)
    return offer.model_dump()


@router.post("/sales")
def create_sale(sale: Sale):
    graph_store.upsert_sale(sale)
    return sale.model_dump()


@router.post("/opportunities")
def create_opportunity(opp: Opportunity):
    graph_store.upsert_opportunity(opp)
    return opp.model_dump()


@router.post("/products")
def create_product(product: Product):
    graph_store.upsert_product(product)
    return product.model_dump()
