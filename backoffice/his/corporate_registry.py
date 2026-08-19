from __future__ import annotations

import json
from pathlib import Path

from .corporate_models import CorporateDocument
from .repository_adapters import RepositoryAdapter


class CorporateDocumentRegistry:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).expanduser().resolve()

    def list(self) -> list[CorporateDocument]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return [CorporateDocument.model_validate(item) for item in payload.get("documents", [])]

    def get(self, document_id: str) -> CorporateDocument:
        for document in self.list():
            if document.document_id == document_id:
                return document
        raise KeyError(document_id)

    def save(self, document: CorporateDocument) -> CorporateDocument:
        documents = self.list()
        for index, existing in enumerate(documents):
            if existing.document_id == document.document_id:
                documents[index] = document
                break
        else:
            documents.append(document)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(
                {"schema_version": 1, "documents": [item.model_dump(mode="json") for item in documents]},
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        temporary.replace(self.path)
        return document

    def refresh_staleness(self, document_id: str, adapters: dict[str, RepositoryAdapter]) -> CorporateDocument:
        document = self.get(document_id)
        stale = False
        for dependency in document.dependencies:
            adapter = adapters.get(dependency.repository_id)
            if adapter is None or adapter.is_stale(dependency):
                stale = True
                break
        if stale:
            document.status = "stale"
            self.save(document)
        return document
