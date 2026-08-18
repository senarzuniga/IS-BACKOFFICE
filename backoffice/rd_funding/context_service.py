"""Context and evidence gateway. Agents never access persistence directly."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from backoffice.intelligence.storage import IntelligenceDB, intelligence_db

from .models import DataConflict, GovernedEntity, InformationLevel, ValidationStatus


class FundingContextService:
    def __init__(self, database: IntelligenceDB | None = None) -> None:
        self.database = database or intelligence_db

    def save(self, entity: GovernedEntity) -> GovernedEntity:
        payload = entity.model_dump(mode="json")
        previous = self.database.get_funding_entity(entity.id)
        if previous and int(previous.get("version", 1)) >= entity.version:
            entity = entity.model_copy(update={"version": int(previous["version"]) + 1, "updated_at": datetime.now(UTC)})
            payload = entity.model_dump(mode="json")
        self.database.save_funding_entity(payload)
        return entity

    def get(self, entity_id: str) -> dict[str, Any] | None:
        return self.database.get_funding_entity(entity_id)

    def list(self, entity_type: str | None = None) -> list[dict[str, Any]]:
        return self.database.get_funding_entities(entity_type=entity_type)

    def relate(self, source_id: str, target_id: str, relation_type: str, evidence_id: str | None = None) -> str:
        relation_id = str(uuid4())
        self.database.save_funding_relation(
            {
                "id": relation_id,
                "source_id": source_id,
                "target_id": target_id,
                "relation_type": relation_type,
                "evidence_id": evidence_id,
                "created_at": datetime.now(UTC).isoformat(),
            }
        )
        return relation_id

    def evidence(self, evidence_id: str) -> dict[str, Any]:
        record = self.get(evidence_id)
        if not record or record.get("entity_type") != "FUNDING_EVIDENCE":
            raise LookupError(f"Evidence not found: {evidence_id}")
        return record

    def assert_final_report_quality(self, funding_call: dict[str, Any]) -> None:
        required = ("organisation", "call_name", "official_url", "verification_date")
        missing = [key for key in required if not funding_call.get(key)]
        if funding_call.get("validation_status") != ValidationStatus.VERIFIED.value:
            missing.append("VERIFIED validation_status")
        if missing:
            raise ValueError("Funding call cannot enter a final report: " + ", ".join(missing))

    def promote_to_actual(self, entity_id: str, evidence_ids: list[str], verified_by: str) -> dict[str, Any]:
        record = self.get(entity_id)
        if not record:
            raise LookupError(entity_id)
        for evidence_id in evidence_ids:
            evidence = self.evidence(evidence_id)
            if evidence.get("validation_status") != ValidationStatus.VERIFIED.value:
                raise ValueError(f"Unverified evidence cannot promote FACT: {evidence_id}")
        record.update(
            {
                "version": int(record.get("version", 1)) + 1,
                "source_type": InformationLevel.ACTUAL.value,
                "evidence_ids": evidence_ids,
                "validation_status": ValidationStatus.VERIFIED.value,
                "verified_at": datetime.now(UTC).isoformat(),
                "verified_by": verified_by,
            }
        )
        self.database.save_funding_entity(record)
        return record

    def create_conflict(self, parameter: str, values: list[Any], evidence_ids: list[str]) -> DataConflict:
        conflict = DataConflict(
            parameter=parameter,
            candidate_values=values,
            candidate_evidence_ids=evidence_ids,
            status="REQUIRES_VERIFICATION",
            evidence_ids=evidence_ids,
            source_type=InformationLevel.ENGINEERING_ASSUMPTION,
            validation_status=ValidationStatus.CONFLICTING,
        )
        return self.save(conflict)
