from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from backoffice.intelligence.storage import IntelligenceDB
from backoffice.rd_funding.bootstrap import write_artifacts
from backoffice.rd_funding.context_service import FundingContextService
from backoffice.rd_funding.engines import (
    BUDGET_CATEGORIES, DOSSIER_SECTIONS, assess_compatibility, build_document_checklist,
    company_classification, company_profile_completeness, create_alert_mission,
    deadline_alerts, design_project, funding_alert_severity, funding_scenarios,
    generate_funding_alerts, liquidity_scenario, qualify_project, score_project_call,
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


def test_liquidity_scenario_separates_grant_loan_and_bridge_need():
    result = liquidity_scenario(
        60000,
        {
            "budget_min_eur": 20000,
            "grant_rate_pct": 40,
            "loan_rate_pct": 30,
            "advance_rate_pct": 50,
            "payment_timing": "50% advance; balance after justification",
        },
    )
    assert result["budget_eligible"] is True
    assert result["grant_eur"] == 24000
    assert result["loan_eur"] == 18000
    assert result["advance_eur"] == 21000
    assert result["bridge_financing_need_eur"] == 21000


def test_regional_call_rejects_project_executed_in_another_region():
    result = score_project_call(
        {"technology_areas": ["ai"], "execution_region": "Cataluña"},
        {"technologies": ["ai"], "territory": "Navarra", "validation_status": "VERIFIED"},
    )
    assert result["dimensions"]["geographical_eligibility"] == 0


def test_partially_repayable_aid_separates_non_repayable_tranche():
    result = liquidity_scenario(
        200000,
        {"budget_min_eur": 175000, "loan_rate_pct": 85, "non_repayable_rate_pct": 10},
    )
    assert result["public_funding_eur"] == 170000
    assert result["grant_eur"] == 17000
    assert result["loan_eur"] == 153000


def test_closed_or_undersized_call_is_no_go():
    project = {"technology_areas": ["ai"], "execution_region": "Cataluña", "preliminary_budget_eur": 60000}
    closed = score_project_call(
        project,
        {"technologies": ["ai"], "territory": "Cataluña", "validation_status": "VERIFIED", "call_status": "CLOSED"},
    )
    undersized = score_project_call(
        project,
        {"technologies": ["ai"], "territory": "Cataluña", "validation_status": "VERIFIED", "call_status": "OPEN", "budget_min_eur": 100000},
    )
    assert closed["decision"] == "NO-GO"
    assert undersized["decision"] == "NO-GO"


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


def test_company_taxonomy_and_alert_center_helpers():
    company = {
        "name": "INGECART",
        "industry": "Industrial engineering",
        "company_size": "SME",
        "legal_form": "Sociedad limitada",
        "technology_areas": ["robotics", "ai", "automation"],
        "women_entrepreneur": False,
        "is_new_company": False,
    }
    assert "INDUSTRIAL COMPANY" in company_classification(company)
    assert "TECHNOLOGY COMPANY" in company_classification(company)
    assert company_profile_completeness({"company_id": "c-1", "name": "INGECART", "legal_form": "SL", "region": "Navarra", "sector": "industry"}) >= 40
    assert funding_alert_severity(15, 85, 90) == "CRITICAL"
    alerts = generate_funding_alerts(company, {"technology_areas": ["robotics", "ai"], "execution_region": "Navarra", "preliminary_budget_eur": 60000}, [{"id": "call-1", "call_name": "Test call", "organisation": "CDTI", "call_status": "OPEN", "validation_status": "VERIFIED", "closing_date": "2026-09-01", "required_documents": ["Budget"]}])
    assert alerts[0]["severity"] in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
    dossier = build_document_checklist()
    assert dossier["application_readiness_pct"] >= 0
    mission = create_alert_mission(alerts[0], project_id="p01", call_id="call-1")
    assert "Verify eligibility" in mission["objective"] or "verify eligibility" in mission["objective"].lower()
