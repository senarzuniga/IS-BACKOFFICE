from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backoffice.his.corporate_models import DeliveryPolicy, DocumentLanguage, PublicationFormat
from backoffice.his.corporate_publishing import CorporatePublishingService


class CorporatePublishRequest(BaseModel):
    repository_id: str
    relative_path: str
    title: str
    client: str
    project: str
    destination: str | None = None
    profile_id: str = "standard"
    formats: list[PublicationFormat] = Field(default_factory=lambda: ["html", "pdf", "docx"])
    languages: list[DocumentLanguage] = Field(default_factory=lambda: ["en", "es"])
    page_size: str = "A4"


router = APIRouter(prefix="/html-intelligence", tags=["html-intelligence"])
_service: CorporatePublishingService | None = None


def _get_service() -> CorporatePublishingService:
    global _service
    if _service is None:
        _service = CorporatePublishingService()
    return _service


@router.get("/status")
def status() -> dict[str, Any]:
    service = _get_service()
    return {
        "status": "operational",
        "repositories": {
            repository_id: {"root": str(adapter.root), "exists": adapter.root.is_dir()}
            for repository_id, adapter in service.adapters.items()
        },
        "registry": str(service.settings.registry_path),
        "output_root": str(service.settings.output_root),
        "formats": ["html", "pdf", "docx", "xlsx", "pptx"],
        "languages": ["en", "es"],
    }


@router.get("/documents")
def documents() -> list[dict[str, Any]]:
    return [item.model_dump(mode="json") for item in _get_service().registry.list()]


@router.get("/documents/{document_id}")
def document(document_id: str) -> dict[str, Any]:
    try:
        return _get_service().registry.get(document_id).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Corporate document not found") from exc


@router.post("/documents", status_code=201)
def publish(payload: CorporatePublishRequest) -> dict[str, Any]:
    try:
        policy = DeliveryPolicy(
            profile_id=payload.profile_id,
            allowed_formats=payload.formats,
            required_languages=payload.languages,
            page_size=payload.page_size,
        )
        result = _get_service().publish_bilingual_html(
            repository_id=payload.repository_id,
            relative_path=payload.relative_path,
            title=payload.title,
            client=payload.client,
            project=payload.project,
            delivery_policy=policy,
            destination=payload.destination,
        )
        return result.model_dump(mode="json")
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/documents/{document_id}/refresh")
def refresh(document_id: str) -> dict[str, Any]:
    service = _get_service()
    try:
        return service.registry.refresh_staleness(document_id, service.adapters).model_dump(mode="json")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Corporate document not found") from exc


@router.post("/documents/{document_id}/package")
def package(document_id: str) -> dict[str, str]:
    try:
        return {"package_path": _get_service().create_delivery_package(document_id)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Corporate document not found") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
