from __future__ import annotations

from typing import Optional

from .memory_store import MemoryStore


class ContextRouter:
    """Resolve application context (company-aware).

    The router maps a company name to the stored company UUID and
    provides helper functions to scope queries and reasoning.
    """

    def __init__(self, memory_store: MemoryStore):
        self.memory_store = memory_store

    def resolve(self, company_name: str) -> Optional[dict]:
        return self.memory_store.get_company_by_name(company_name)
