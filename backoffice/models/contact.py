"""Contact canonical model."""
from __future__ import annotations
from typing import Optional
from pydantic import Field
from .base import BaseEntity


class Contact(BaseEntity):
    client_id: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_decision_maker: bool = False
