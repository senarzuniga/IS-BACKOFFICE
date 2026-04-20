"""Opportunity canonical model."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import Field
from .base import BaseEntity


class Opportunity(BaseEntity):
    client_id: str
    title: str
    stage: str = "qualification"  # qualification | proposal | negotiation | closed_won | closed_lost
    estimated_value: Optional[float] = None
    currency: str = "EUR"
    probability: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    expected_close_date: Optional[datetime] = None
    outcome: Optional[str] = None
