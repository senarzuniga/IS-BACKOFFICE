"""Relation types and Relation model."""
from __future__ import annotations
from enum import Enum
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from backoffice.models.base import _uuid, _now


class RelationType(str, Enum):
    CLIENT_HAS_CONTACT = "CLIENT_HAS_CONTACT"
    CLIENT_HAS_OFFER = "CLIENT_HAS_OFFER"
    CLIENT_HAS_SALE = "CLIENT_HAS_SALE"
    CLIENT_HAS_OPPORTUNITY = "CLIENT_HAS_OPPORTUNITY"
    OFFER_LEADS_TO_SALE = "OFFER_LEADS_TO_SALE"
    OPPORTUNITY_LEADS_TO_SALE = "OPPORTUNITY_LEADS_TO_SALE"
    SALE_INCLUDES_PRODUCT = "SALE_INCLUDES_PRODUCT"
    OFFER_INCLUDES_PRODUCT = "OFFER_INCLUDES_PRODUCT"
    DOCUMENT_REFERENCES_CLIENT = "DOCUMENT_REFERENCES_CLIENT"


class Relation(BaseModel):
    relation_id: str = Field(default_factory=_uuid)
    relation_type: RelationType
    source_id: str
    target_id: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_now)
