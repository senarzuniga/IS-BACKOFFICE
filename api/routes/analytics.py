"""Analytics API routes."""
from fastapi import APIRouter
from backoffice.analytics.pipeline_scoring import PipelineScorer
from backoffice.analytics.forecasting import Forecaster
from backoffice.analytics.account_health import AccountHealthScorer
from backoffice.analytics.offer_validation import OfferValidator
from backoffice.analytics.portfolio import PortfolioAnalyzer
from api.state import graph_store

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/pipeline")
def pipeline_summary():
    return PipelineScorer(graph_store).pipeline_summary()


@router.get("/forecast")
def forecast(periods: int = 3):
    return Forecaster(graph_store).forecast_next_period(periods=periods)


@router.get("/conversion")
def conversion():
    return Forecaster(graph_store).conversion_probability()


@router.get("/accounts/health")
def account_health():
    return AccountHealthScorer(graph_store).score_all_clients()


@router.get("/accounts/{client_id}/health")
def client_health(client_id: str):
    return AccountHealthScorer(graph_store).score_client(client_id)


@router.get("/offers/validation")
def offer_validation():
    return OfferValidator(graph_store).validate_all_offers()


@router.get("/portfolio")
def portfolio():
    return PortfolioAnalyzer(graph_store).classify_products()
