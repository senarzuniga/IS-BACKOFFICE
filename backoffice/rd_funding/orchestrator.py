"""Specialist-agent routing over the governed funding context service."""
from __future__ import annotations

from typing import Any

from .context_service import FundingContextService
from .engines import assess_compatibility, qualify_project, score_project_call


AGENTS = (
    "R&D DISCOVERY AGENT", "R&D QUALIFICATION AGENT", "TECHNOLOGY ASSESSMENT AGENT",
    "TRL ASSESSMENT AGENT", "FUNDING DISCOVERY AGENT", "NAVARRA FUNDING AGENT",
    "CDTI FUNDING AGENT", "EU FUNDING AGENT", "FUNDING ELIGIBILITY AGENT",
    "FUNDING COMPATIBILITY AGENT", "BUDGET AGENT", "FUNDING SCORING AGENT",
    "APPLICATION DESIGN AGENT", "JUSTIFICATION AGENT", "FUNDING MONITORING AGENT",
    "EVIDENCE VERIFICATION AGENT",
)


class RDFundingOrchestrator:
    def __init__(self, context: FundingContextService | None = None) -> None:
        self.context = context or FundingContextService()

    def qualify(self, project_id: str) -> dict[str, Any]:
        project = self._require(project_id, "CLIENT_PROJECT")
        evidence = [self.context.evidence(item) for item in project.get("evidence_ids", [])]
        return {"agent": "R&D QUALIFICATION AGENT", **qualify_project(project, evidence)}

    def match(self, project_id: str, funding_call_id: str) -> dict[str, Any]:
        project = self._require(project_id, "CLIENT_PROJECT")
        call = self._require(funding_call_id, "FUNDING_CALL")
        return {"agent": "FUNDING SCORING AGENT", **score_project_call(project, call)}

    def compatibility(self, funding_call_ids: list[str], cost_ids: list[str]) -> dict[str, Any]:
        calls = [self._require(item, "FUNDING_CALL") for item in funding_call_ids]
        return {"agent": "FUNDING COMPATIBILITY AGENT", **assess_compatibility(calls, cost_ids)}

    def application_gate(self, funding_call_id: str, consultant_approved: bool) -> dict[str, Any]:
        call = self._require(funding_call_id, "FUNDING_CALL")
        self.context.assert_final_report_quality(call)
        if not consultant_approved:
            return {"status": "PENDING_CONSULTANT_REVIEW", "submission_allowed": False}
        return {"status": "APPROVED_FOR_DOSSIER_PREPARATION", "submission_allowed": False}

    def _require(self, entity_id: str, expected_type: str) -> dict[str, Any]:
        entity = self.context.get(entity_id)
        if not entity or entity.get("entity_type") != expected_type:
            raise LookupError(f"{expected_type} not found: {entity_id}")
        return entity
