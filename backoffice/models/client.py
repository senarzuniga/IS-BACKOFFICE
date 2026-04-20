"""Client canonical model."""
from __future__ import annotations
from typing import Optional, List
from pydantic import Field
from .base import BaseEntity


class Client(BaseEntity):
    name: str
    normalized_name: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    currency: str = "EUR"
    tags: List[str] = Field(default_factory=list)
    annual_revenue: Optional[float] = None
    account_health_score: Optional[float] = None
