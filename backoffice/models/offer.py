"""Offer canonical model."""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import Field
from .base import BaseEntity


class Offer(BaseEntity):
    client_id: str
    title: str
    status: str = "draft"  # draft | sent | accepted | rejected | expired
    total_value: Optional[float] = None
    currency: str = "EUR"
    items: List[Dict[str, Any]] = Field(default_factory=list)
    valid_until: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    pricing_anomaly: bool = False
    anomaly_reason: Optional[str] = None
