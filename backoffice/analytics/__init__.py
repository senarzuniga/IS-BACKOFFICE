from .pipeline_scoring import PipelineScorer
from .forecasting import Forecaster
from .account_health import AccountHealthScorer
from .offer_validation import OfferValidator
from .portfolio import PortfolioAnalyzer
from .engine import AIAnalyticsEngine

try:
    from .ingecart_monitoring import (
        load_monitoring_blueprint,
        generate_monitoring_snapshot,
        generate_instant_offer,
        suggest_spare_parts,
        build_request_alert,
        get_scope_label,
        get_scope_options,
        ROLE_PANELS,
        FORMULA_LIBRARY,
        SPARE_PART_CATALOG,
    )
except Exception:  # pragma: no cover - optional feature fallback
    load_monitoring_blueprint = None
    generate_monitoring_snapshot = None
    generate_instant_offer = None
    suggest_spare_parts = None
    build_request_alert = None
    get_scope_label = None
    get_scope_options = None
    ROLE_PANELS = {}
    FORMULA_LIBRARY = []
    SPARE_PART_CATALOG = []

__all__ = [
    "PipelineScorer", "Forecaster", "AccountHealthScorer",
    "OfferValidator", "PortfolioAnalyzer", "AIAnalyticsEngine",
    # Ingecart monitoring
    "load_monitoring_blueprint", "generate_monitoring_snapshot",
    "generate_instant_offer", "suggest_spare_parts", "build_request_alert",
    "get_scope_label", "get_scope_options",
    "ROLE_PANELS", "FORMULA_LIBRARY", "SPARE_PART_CATALOG",
]
