"""Standard Product Offer Engine (SPOE) package."""

from .models import OfferInput, ProductTemplate
from .catalog import load_product_catalog
from .calculator import calculate_sr1400_bom
from .coordinator import supervise_offer_quality
from .documents import generate_offer_documents
from .knowledge import build_knowledge_package
from .knowledge_hub_store import persist_offer_record
from .architecture import evaluate_architecture_alternatives
from .mission_manager import run_ame_iteration
from .governance import update_governance_artifacts

__all__ = [
    "OfferInput",
    "ProductTemplate",
    "load_product_catalog",
    "calculate_sr1400_bom",
    "supervise_offer_quality",
    "generate_offer_documents",
    "build_knowledge_package",
    "persist_offer_record",
    "evaluate_architecture_alternatives",
    "run_ame_iteration",
    "update_governance_artifacts",
]
