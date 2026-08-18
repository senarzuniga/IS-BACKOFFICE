"""Governed entities for the CTA Industrial R&D Funding Engine."""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

from pydantic import Field, model_validator

from backoffice.models.base import BaseEntity


class InformationLevel(str, Enum):
    ACTUAL = "LEVEL_1_ACTUAL"
    CALIBRATED = "LEVEL_2_CALIBRATED"
    ENGINEERING_ASSUMPTION = "LEVEL_3_ENGINEERING_ASSUMPTION"


class ValidationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    OUTDATED = "OUTDATED"
    CONFLICTING = "CONFLICTING"
    MISSING_SOURCE = "MISSING_SOURCE"


class GovernedEntity(BaseEntity):
    entity_type: str
    version: int = Field(default=1, ge=1)
    status: str = "DRAFT"
    owner: str = "CTA"
    source_type: InformationLevel = InformationLevel.ENGINEERING_ASSUMPTION
    source_document: Optional[str] = None
    source_location: Optional[str] = None
    evidence_ids: list[str] = Field(default_factory=list)
    validation_status: ValidationStatus = ValidationStatus.UNVERIFIED
    verified_at: Optional[datetime] = None

    @model_validator(mode="after")
    def prevent_untraced_actual(self) -> "GovernedEntity":
        if self.source_type == InformationLevel.ACTUAL and not self.evidence_ids:
            raise ValueError("LEVEL_1_ACTUAL requires at least one evidence_id")
        if self.validation_status == ValidationStatus.VERIFIED and not self.verified_at:
            raise ValueError("VERIFIED entities require verified_at")
        return self


class FundingEvidence(GovernedEntity):
    entity_type: str = "FUNDING_EVIDENCE"
    source_text: str = ""
    parameter: Optional[str] = None
    value: Any = None
    unit: Optional[str] = None
    extraction_method: str = "manual"
    verified_by: Optional[str] = None
    official_source: bool = False


class FundingClient(GovernedEntity):
    entity_type: str = "CLIENT"
    name: str
    country: str = "Spain"
    region: str = "Navarra"
    industry: str = "Industrial engineering"


class ClientProject(GovernedEntity):
    entity_type: str = "CLIENT_PROJECT"
    client_id: str
    code: str
    name: str
    product: str = ""
    technology_areas: list[str] = Field(default_factory=list)
    problem: str = ""
    current_state: str = ""
    target_state: str = ""
    innovation: str = ""
    technological_uncertainties: list[str] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)
    expected_result: str = ""
    market: str = "Industrial"
    initial_trl: Optional[int] = Field(default=None, ge=1, le=9)
    target_trl: Optional[int] = Field(default=None, ge=1, le=9)
    duration_months: Optional[int] = Field(default=None, ge=1)
    preliminary_budget_eur: Optional[float] = Field(default=None, ge=0)
    team: list[str] = Field(default_factory=list)
    technological_partners: list[str] = Field(default_factory=list)
    available_documents: list[str] = Field(default_factory=list)
    parent_project_id: Optional[str] = None


class FundingCall(GovernedEntity):
    entity_type: str = "FUNDING_CALL"
    funding_id: str
    organisation: str
    program: str
    call_name: str
    official_url: str
    call_status: str = "UNKNOWN"
    opening_date: Optional[date] = None
    closing_date: Optional[date] = None
    beneficiaries: list[str] = Field(default_factory=list)
    territory: str = ""
    sectors: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    trl_min: Optional[int] = None
    trl_max: Optional[int] = None
    budget_min_eur: Optional[float] = None
    budget_max_eur: Optional[float] = None
    funding_rate_pct: Optional[float] = None
    max_aid_eur: Optional[float] = None
    aid_types: list[str] = Field(default_factory=list)
    eligible_costs: list[str] = Field(default_factory=list)
    incentive_effect_required: Optional[bool] = None
    minimis: Optional[bool] = None
    evaluation_criteria: list[str] = Field(default_factory=list)
    verification_date: Optional[date] = None

    def usable_in_final_report(self) -> bool:
        return bool(
            self.organisation and self.call_name and self.official_url
            and self.verification_date and self.validation_status == ValidationStatus.VERIFIED
        )


class ProjectBudget(GovernedEntity):
    entity_type: str = "PROJECT_BUDGET"
    project_id: str
    total_eur: float = Field(ge=0)
    currency: str = "EUR"


class EligibleCost(GovernedEntity):
    entity_type: str = "ELIGIBLE_COST"
    project_id: str
    work_package_id: Optional[str] = None
    task_id: Optional[str] = None
    funding_call_id: Optional[str] = None
    category: str
    amount_eur: float = Field(ge=0)
    eligibility_status: str = "UNKNOWN"


class FundingScore(GovernedEntity):
    entity_type: str = "FUNDING_SCORE"
    project_id: str
    funding_call_id: str
    dimensions: dict[str, float]
    score: float = Field(ge=0, le=100)
    decision: str
    rationale: list[str] = Field(default_factory=list)


class FundingCompatibility(GovernedEntity):
    entity_type: str = "FUNDING_COMPATIBILITY"
    funding_call_ids: list[str]
    result: str
    rationale: list[str] = Field(default_factory=list)


class FundingDeadline(GovernedEntity):
    entity_type: str = "FUNDING_DEADLINE"
    funding_call_id: str
    deadline_type: str
    due_date: date
    alert_days: list[int] = Field(default_factory=lambda: [180, 120, 90, 60, 30, 15, 7, 0])


class FundingMission(GovernedEntity):
    entity_type: str = "FUNDING_MISSION"
    objective: str
    project_id: Optional[str] = None
    funding_call_id: Optional[str] = None
    assigned_agent: str
    stage: str = "DISCOVERY"
    next_action: str
    deliverable: str
    blocking_reason: Optional[str] = None


class DataConflict(GovernedEntity):
    entity_type: str = "DATA_CONFLICT"
    parameter: str
    candidate_values: list[Any]
    candidate_evidence_ids: list[str]
    resolution_mission_id: Optional[str] = None


def _simple_entity(name: str):
    return type(name, (GovernedEntity,), {"__annotations__": {"entity_type": str}, "entity_type": name.upper()})


# The remaining mission entities share the governed envelope and accept domain
# payload through explicit future extensions, while retaining stable type names.
for _name in (
    "ProjectVersion", "ProjectDiscoveryCard", "TechnicalAssessment", "RDAssessment",
    "TechnologyAssessment", "TRLAssessment", "StateOfArt", "TechnologicalUncertainty",
    "InnovationObjective", "Hypothesis", "WorkPackage", "Task", "Milestone", "Deliverable",
    "ProjectRisk", "ProjectResource", "TechnologicalPartner", "FundingProgram",
    "FundingRequirement", "FundingEligibility", "FundingOpportunity", "FundingApplication",
    "FundingSource", "FundingScenario", "FundingDecision", "ApplicationDossier",
    "Justification", "FundingMonitoring",
):
    globals()[_name] = _simple_entity(_name)
