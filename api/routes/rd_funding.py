from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backoffice.rd_funding.bootstrap import bootstrap_ingecart
from backoffice.rd_funding.context_service import FundingContextService
from backoffice.rd_funding.engines import build_document_checklist, generate_funding_alerts
from backoffice.rd_funding.models import ClientProject
from backoffice.rd_funding.orchestrator import AGENTS, RDFundingOrchestrator


class ProjectCreateRequest(BaseModel):
    client_id: str
    code: str
    name: str
    product: str = ""
    technology_areas: list[str] = Field(default_factory=list)
    problem: str = ""
    target_state: str = ""
    innovation: str = ""
    technological_uncertainties: list[str] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)
    preliminary_budget_eur: float | None = None


router = APIRouter(prefix="/rd-funding", tags=["rd-funding"])
_context = FundingContextService()
_orchestrator = RDFundingOrchestrator(_context)


@router.get("/status")
def status() -> dict[str, Any]:
    return {
        "status": "operational_with_information_gaps",
        "clients": len(_context.list("CLIENT")),
        "projects": len(_context.list("CLIENT_PROJECT")),
        "funding_calls": len(_context.list("FUNDING_CALL")),
        "missions": len(_context.list("FUNDING_MISSION")),
        "agents": list(AGENTS),
        "submission_policy": "HUMAN_APPROVAL_REQUIRED",
    }


@router.post("/bootstrap/ingecart")
def bootstrap() -> dict[str, Any]:
    return bootstrap_ingecart(_context)


@router.get("/projects")
def projects() -> list[dict[str, Any]]:
    return _context.list("CLIENT_PROJECT")


@router.post("/projects")
def create_project(payload: ProjectCreateRequest) -> dict[str, Any]:
    return _context.save(ClientProject(**payload.model_dump())).model_dump(mode="json")


@router.get("/funding-calls")
def funding_calls() -> list[dict[str, Any]]:
    return _context.list("FUNDING_CALL")


@router.post("/projects/{project_id}/qualify")
def qualify(project_id: str) -> dict[str, Any]:
    try:
        return _orchestrator.qualify(project_id)
    except (LookupError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/projects/{project_id}/match/{funding_call_id}")
def match(project_id: str, funding_call_id: str) -> dict[str, Any]:
    try:
        return _orchestrator.match(project_id, funding_call_id)
    except (LookupError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/alerts")
def alerts(project_id: str | None = None) -> list[dict[str, Any]]:
    project = None
    if project_id:
        project = _context.get(project_id)
    calls = _context.list("FUNDING_CALL")
    return generate_funding_alerts(project=project, calls=calls)


@router.get("/projects/{project_id}/dossier")
def dossier(project_id: str) -> dict[str, Any]:
    project = _context.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return build_document_checklist(project=project)
