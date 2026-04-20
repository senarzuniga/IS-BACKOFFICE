"""Sale canonical model."""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import Field
from .base import BaseEntity


class Sale(BaseEntity):
    client_id: str
    opportunity_id: Optional[str] = None
    offer_id: Optional[str] = None
    amount: float
    currency: str = "EUR"
    amount_eur: Optional[float] = None  # normalized to EUR
    sale_date: Optional[datetime] = None
    product_ids: List[str] = Field(default_factory=list)
    line_items: List[Dict[str, Any]] = Field(default_factory=list)
    validated: bool = False
