from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from backoffice.intelligence.storage import IntelligenceDB
from backoffice.rd_funding.bootstrap import write_artifacts
from backoffice.rd_funding.context_service import FundingContextService
from backoffice.rd_funding.engines import (
    BUDGET_CATEGORIES, DOSSIER_SECTIONS, assess_compatibility, deadline_alerts,
    design_project, funding_scenarios, qualify_project, score_project_call,
)
from backoffice.rd_funding.models import (
    ClientProject, FundingCall, FundingEvidence, InformationLevel, ValidationStatus,
)
from backoffice.rd_funding.orchestrator import AGENTS, RDFundingOrchestrator


@pytest.fixture
def context(tmp_path):
    return FundingContextService(IntelligenceDB(tmp_path / "funding_test.db"))


def verified_evidence(context):
    return context.save(
        FundingEvidence(
            id="ev-1", source_type=InformationLevel.ENGINEERING_ASSUMPTION,
            source_document="client.pdf", source_location="page 3 / section 2",
            source_text="Documented technological uncertainty", official_source=False,
            validation_status=ValidationStatus.VERIFIED, verified_at=datetime.now(UTC),
        )
    )


def project_record(context, evidence_id="ev-1"):
    return context.save(
        ClientProject(
            id="p01", client_id="ingecart", code="P01", name="INGETRANS",
            technology_areas=["industrial software", "automation"],
            technological_uncertainties=["coordination", "variable latency"],
            hypotheses=["adaptive control improves robustness"], initial_trl=3, target_trl=6,
            preliminary_budget_eur=500000, evidence_ids=[evidence_id],
        )
    )


def call_record(context, verified=True):
    return context.save(
        FundingCall(
            id="call-1", funding_id="CDTI-PID", organisation="CDTI", program="PID",
            call_name="PID test fixture", official_url="https://www.cdti.es/ayudas",
            territory="Spain", technologies=["industrial software", "automation"],
            eligible_costs=["Personal interno", "Prototipos"], funding_rate_pct=40,
            verification_date=date.today() if verified else None,
            validation_status=ValidationStatus.VERIFIED if verified else ValidationStatus.UNVERIFIED,
            verified_at=datetime.now(UTC) if verified else None,
        )
    )


def test_project_creation_and_versioning(context):
    verified_evidence(context)
    first = project_record(context)
    second = context.save(first.model_copy(update={"status": "ASSESSMENT"}))
    assert second.version == 2
    assert context.get("p01")["status"] == "ASSESSMENT"


def test_project_qualification_requires_verified_evidence(context):
    evidence = verified_evidence(context)
    project = project_record(context, evidence.id)
    result = RDFundingOrchestrator(context).qualify(project.id)
    assert result["classification"] == "I+D LIKELY"
    assert result["evidence_ids"] == [evidence.id]


def test_evidence_traceability_blocks_assumption_as_fact(context):
    evidence = context.save(FundingEvidence(id="ev-u", source_text="benchmark"))
    project = project_record(context, evidence.id)
    with pytest.raises(ValueError, match="Unverified evidence"):
        context.promote_to_actual(project.id, [evidence.id], "consultant")


def test_funding_ingestion_keeps_official_source(context):
    call = call_record(context)
    stored = context.get(call.id)
    assert stored["official_url"].startswith("https://www.cdti.es")
    assert stored["validation_status"] == "VERIFIED"


def test_funding_classification_unverified_is_watch():
    result = score_project_call(
        {"technology_areas": ["ai"], "technological_uncertainties": ["x"]},
        {"technologies": ["ai"], "territory": "Spain", "validation_status": "UNVERIFIED"},
    )
    assert result["decision"] == "WATCH"


def test_eligibility_final_report_gate(context):
    call = call_record(context, verified=False)
    with pytest.raises(ValueError, match="cannot enter a final report"):
        context.assert_final_report_quality(context.get(call.id))


def test_matching_scores_all_dimensions(context):
    evidence = verified_evidence(context)
    project = project_record(context, evidence.id)
    call = call_record(context)
    result = RDFundingOrchestrator(context).match(project.id, call.id)
    assert len(result["dimensions"]) == 13
    assert 0 <= result["score"] <= 100


def test_scoring_has_explainable_decision(context):
    evidence = verified_evidence(context)
    project = project_record(context, evidence.id)
    call = call_record(context)
    result = RDFundingOrchestrator(context).match(project.id, call.id)
    assert result["decision"] in {"GO", "STRATEGIC REDESIGN", "NO-GO"}
    assert result["rationale"]


def test_budget_and_financial_scenarios():
    assert "Centros tecnológicos" in BUDGET_CATEGORIES
    scenarios = funding_scenarios(100000, 40)
    assert [item["name"] for item in scenarios] == ["CONSERVATIVE", "BASE", "OPTIMISTIC"]
    assert scenarios[1]["client_contribution_eur"] == 60000


def test_compatibility_detects_double_financing():
    calls = [{"validation_status": "VERIFIED", "minimis": False}] * 2
    result = assess_compatibility(calls, ["cost-1", "cost-1"])
    assert result["result"] == "NOT COMPATIBLE"


def test_calendar_alerts():
    today = date(2026, 8, 17)
    alerts = deadline_alerts(today + timedelta(days=15), today)
    assert next(item for item in alerts if item["days"] == 15)["due"]
    assert not next(item for item in alerts if item["days"] == 7)["due"]


def test_report_generation(tmp_path, monkeypatch):
    import backoffice.rd_funding.bootstrap as module
    monkeypatch.setattr(module, "REPORT_ROOT", tmp_path / "reports")
    monkeypatch.setattr(module, "KNOWLEDGE_ROOT", tmp_path / "knowledge")
    payload = {"matrix": [{"project_code": "P01", "call_id": "call", "score": 70, "decision": "GO"}], "missions": []}
    write_artifacts(payload)
    assert (tmp_path / "reports" / "PROJECT_FUNDING_MATRIX.md").exists()
    assert (tmp_path / "reports" / "EXECUTIVE_FUNDING_DASHBOARD.md").exists()


def test_agent_orchestration_and_human_gate(context):
    assert len(AGENTS) == 16
    call = call_record(context)
    result = RDFundingOrchestrator(context).application_gate(call.id, consultant_approved=False)
    assert result == {"status": "PENDING_CONSULTANT_REVIEW", "submission_allowed": False}


def test_project_design_is_editable_ai_proposal():
    design = design_project({"technology_areas": ["robotics", "amr"]})
    assert len(design["work_packages"]) == 4
    assert design["approval_status"] == "AI_PROPOSAL_REQUIRES_CONSULTANT_REVIEW"
    assert tuple(design["dossier_sections"]) == DOSSIER_SECTIONS


def test_ingecart_p01_end_to_end(context, tmp_path, monkeypatch):
    evidence = verified_evidence(context)
    project = project_record(context, evidence.id)
    call = call_record(context)
    orchestrator = RDFundingOrchestrator(context)
    qualification = orchestrator.qualify(project.id)
    match = orchestrator.match(project.id, call.id)
    strategy = funding_scenarios(500000, 40)
    assert qualification["classification"] == "I+D LIKELY"
    assert match["score"] > 50
    assert strategy[1]["potential_public_funding_eur"] == 200000