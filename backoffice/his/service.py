from __future__ import annotations

from pathlib import Path
from typing import Any, TYPE_CHECKING

from .repository import DocumentRepository

if TYPE_CHECKING:
    from .studio import HtmlIntelligenceStudio


class HtmlDocumentService:
    """Business/service layer for HIS, used by the facade for stable API."""

    def __init__(self, repository: DocumentRepository, facade: "HtmlIntelligenceStudio") -> None:
        self.repository = repository
        self.facade = facade

    def list_documents(self) -> list[dict[str, Any]]:
        return self.repository.list()

    def get_document(self, document_model_path: str) -> dict[str, Any]:
        return self.repository.get(document_model_path)

    def open_document(self, document_model_path: str) -> dict[str, Any]:
        return self.repository.open(document_model_path)

    def delete_document(self, document_model_path: str) -> bool:
        return self.repository.delete(document_model_path)

    def duplicate_document(self, document_model_path: str) -> dict[str, Any]:
        return self.repository.duplicate(document_model_path)

    def save_document(self, document_model_path: str, updates: dict[str, Any]) -> dict[str, Any]:
        return self.repository.save(document_model_path, updates)

    def generate_html(self, **kwargs: Any) -> dict[str, Any]:
        return self.facade.create_document(**kwargs)

    def preview_document(self, document_model_path: str) -> dict[str, Any]:
        versions = self.repository.list_versions(document_model_path)
        html_path = ""
        if versions:
            html_path = versions[-1].get("output_files", {}).get("html", "")
        return {
            "document_model_path": document_model_path,
            "html_path": html_path,
        }

    def publish_document(self, document_model_path: str, author: str = "Mission Manager") -> dict[str, Any]:
        return self.facade.publish_document(document_model_path, author=author)

    def list_versions(self, document_model_path: str) -> list[dict[str, Any]]:
        return self.repository.list_versions(document_model_path)

    def restore_version(self, document_model_path: str, version_number: int) -> dict[str, Any]:
        return self.repository.restore_version(document_model_path, version_number)

    def search(self, query: str, limit: int = 200) -> list[dict[str, Any]]:
        return self.repository.search(query, limit=limit)

    def statistics(self) -> dict[str, Any]:
        return self.repository.statistics()

    def quality_report(self, document_model_path: str) -> dict[str, Any]:
        return self.repository.quality_report(document_model_path)
