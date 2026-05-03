"""Orchestration routes for run-cycle and multi-agent execution."""
from __future__ import annotations

from fastapi import APIRouter

from backoffice import CommercialIntelligenceOS
from backoffice.agents import MultiAgentOrchestrator
from shared.schemas import AgentRunResponse, RunCycleRequest, RunCycleResponse

router = APIRouter(prefix="/orchestration", tags=["orchestration"])
_osys = CommercialIntelligenceOS()
_multi = MultiAgentOrchestrator()


@router.post("/run", response_model=RunCycleResponse)
def run_cycle(payload: RunCycleRequest) -> RunCycleResponse:
    metadata: dict[str, str] = {}
    if payload.classification:
        metadata["classification"] = payload.classification

    record = _osys.ingestion.ingest_record(
        source_type=payload.source_type,
        content=payload.content,
        source_id=payload.source_id,
        **metadata,
    )
    result = _osys.run_cycle(
        [record],
        proactive_mode=payload.proactive_mode,
        autolearning_mode=payload.autolearning_mode,
        strict_mode=payload.strict_mode,
    )
    return RunCycleResponse(status=result.get("status", "ok"), result=result)


@router.post("/agents/run", response_model=AgentRunResponse)
def run_agents(payload: RunCycleRequest) -> AgentRunResponse:
    result = _multi.run(payload.model_dump())
    return AgentRunResponse(**result)
