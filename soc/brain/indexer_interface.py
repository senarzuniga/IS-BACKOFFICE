from __future__ import annotations

from typing import Protocol, Iterable, Dict, Any


class IndexerInterface(Protocol):
    """Minimal indexer interface used by the Brain package.

    This file is intentionally lightweight: it provides the protocol so
    imports of `soc.brain` succeed during test discovery. Implementations
    may be provided separately for production indexing.
    """

    def index(self, company_uuid: str, documents: Iterable[Dict[str, Any]]) -> None:  # pragma: no cover - interface
        ...

    def search(self, company_uuid: str, query: str, limit: int = 10):  # pragma: no cover - interface
        ...
