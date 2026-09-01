"""Service Proposal Engine (SPE) — backoffice package."""

from .database import SPEDatabase
from .models import Proposal, ServiceItem, ProposalStatus
from .numbering import ProposalNumbering
from .generator import ProposalHTMLGenerator
from .mission_manager import SPEMissionManager
from .validator import validate_proposal_document
from .word_generator import ProposalWordGenerator
from .annual_offer_factory import build_smart_plant_annual_proposals

__all__ = [
    "SPEDatabase",
    "Proposal",
    "ServiceItem",
    "ProposalStatus",
    "ProposalNumbering",
    "ProposalHTMLGenerator",
    "SPEMissionManager",
    "validate_proposal_document",
    "ProposalWordGenerator",
    "build_smart_plant_annual_proposals",
]
