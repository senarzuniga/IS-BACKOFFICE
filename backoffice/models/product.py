"""Product canonical model."""
from __future__ import annotations
from typing import Optional, List
from pydantic import Field
from .base import BaseEntity


class Product(BaseEntity):
    name: str
    normalized_name: Optional[str] = None
    category: Optional[str] = None
    lifecycle_stage: str = "active"  # commodity | growth | decline | innovation | active
    unit_price: Optional[float] = None
    currency: str = "EUR"
    tags: List[str] = Field(default_factory=list)
