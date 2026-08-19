"""Reproducible first-client bootstrap and evidence-governed report generation."""
from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from .context_service import FundingContextService
from .catalog import CATALOG_CALLS
from .engines import funding_scenarios, liquidity_scenario
from .models import (
    ClientProject, FundingCall, FundingClient, FundingEvidence, FundingMission,
    InformationLevel, ValidationStatus,
)
from .orchestrator import RDFundingOrchestrator


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_ROOT = REPO_ROOT / "reports" / "rd_funding"
KNOWLEDGE_ROOT = REPO_ROOT / "knowledge_hub" / "rd_funding"
OBSOLETE_PROJECT_IDS = {"ingecart-p02a", "ingecart-p02b"}
OBSOLETE_CALL_IDS = {"call-navarra-rd", "call-cdti-pid", "call-eu-horizon"}
OBSOLETE_MISSION_IDS = {f"mission-verify-{call_id}" for call_id in OBSOLETE_CALL_IDS}


PROJECTS = (
    {
        "id": "ingecart-p01", "code": "P01", "name": "INGETRANS SOFTWARE & CONTROL",
        "product": "INGETRANS", "technology_areas": ["industrial software", "automation", "control"],
        "problem": "Control and integration of reel logistics equipment and one or two corrugators.",
        "innovation": "Integrated movement, identification, weighing and dual-reel transfer control.",
        "technological_uncertainties": ["Multi-equipment coordination under variable plant conditions"],
        "hypotheses": ["Context-aware control can improve robust reel-flow coordination"],
        "preliminary_budget_eur": 60000,
        "execution_region": "Navarra",
        "available_documents": ["PROYECTOS PARA GESTION AYUDAS Y RECURSOS INGENIERIA I+D (missing file)"],
    },
    {
        "id": "ingecart-p02", "code": "P02", "name": "AI PRODUCTION FLOW & ERP INTEGRATION",
        "product": "Industrial flow management software", "technology_areas": ["ai", "industrial software", "erp", "smart manufacturing"],
        "problem": "Coordinate corrugator, RDC, finishing, palletising, WIP and dispatch against ERP orders.",
        "innovation": "Evidence-based dynamic sequencing, WIP control and ERP-neutral integration.",
        "technological_uncertainties": ["Robust rescheduling under variable plant conditions", "Explainable multi-equipment optimisation"],
        "hypotheses": ["Dynamic sequencing can reduce starvation and WIP without degrading OTIF"],
        "preliminary_budget_eur": 60000,
        "execution_region": "Navarra",
    },
    {
        "id": "ingecart-p03", "code": "P03", "name": "AI PERIPHERAL EQUIPMENT CONTROL",
        "product": "Industrial equipment coordination platform", "technology_areas": ["ai", "automation", "industrial software", "intralogistics"],
        "problem": "Coordinate RDC, FFG, finishing, WIP transfers, palletisers and internal transport.",
        "innovation": "Domain agents for planning, bottlenecks, transport, maintenance and simulation.",
        "technological_uncertainties": ["Safe real-time coordination of heterogeneous equipment", "Reliable congestion prediction"],
        "hypotheses": ["Constrained agent recommendations can improve throughput while preserving human control"],
        "preliminary_budget_eur": 60000,
        "execution_region": "Navarra",
    },
    {
        "id": "ingecart-p04", "code": "P04", "name": "REAL-TIME INTELLIGENT WAREHOUSE",
        "product": "GPS/RTLS warehouse management", "technology_areas": ["ai", "industrial software", "rtls", "warehouse automation"],
        "problem": "Provide real-time location, stock, movement and decision support for industrial warehouses.",
        "innovation": "Real-time warehouse model combining location evidence, operational events and AI recommendations.",
        "technological_uncertainties": ["Reliable industrial indoor positioning", "Consistent fusion of ERP and real-time events"],
        "hypotheses": ["Evidence-linked RTLS events can reduce search and inventory discrepancies"],
        "preliminary_budget_eur": 60000,
        "execution_region": "Navarra",
        "available_documents": ["IAR folder", "Of. 26-05-073V0 (Ingecart) Real Time Warehouse Management.pdf"],
    },
)


def bootstrap_ingecart(context: FundingContextService | None = None) -> dict[str, Any]:
    context = context or FundingContextService()
    orchestrator = RDFundingOrchestrator(context)
    for entity_type, obsolete_ids, model in (
        ("CLIENT_PROJECT", OBSOLETE_PROJECT_IDS, ClientProject),
        ("FUNDING_CALL", OBSOLETE_CALL_IDS, FundingCall),
        ("FUNDING_MISSION", OBSOLETE_MISSION_IDS, FundingMission),
    ):
        for record in context.list(entity_type):
            if record["id"] in obsolete_ids and record.get("status") != "ARCHIVED":
                context.save(model.model_validate(record).model_copy(update={"status": "ARCHIVED"}))
    evidence = context.save(
        FundingEvidence(
            id="evidence-ingecart-project-brief-missing",
            status="INFORMATION_GAP",
            source_type=InformationLevel.ENGINEERING_ASSUMPTION,
            source_document="PROYECTOS PARA GESTION AYUDAS Y RECURSOS INGENIERIA I+D",
            source_location="Requested attachment not present in workspace or conversation attachments",
            source_text="Document named by the client mission; original bytes and page references unavailable.",
            extraction_method="mission_context_only",
            confidence=0.2,
            validation_status=ValidationStatus.MISSING_SOURCE,
            official_source=False,
        )
    )

    client = context.save(
        FundingClient(
            id="client-ingecart",
            name="INGECART",
            status="ACTIVE",
            source_type=InformationLevel.ACTUAL,
            source_document="CTA mission brief",
            source_location="First client declaration",
            evidence_ids=[evidence.id],
            confidence=0.9,
            validation_status=ValidationStatus.UNVERIFIED,
        )
    )

    projects = []
    for item in PROJECTS:
        project = context.save(
            ClientProject(
                **item,
                client_id="client-ingecart",
                status="DISCOVERY",
                owner="CTA",
                source_type=InformationLevel.ENGINEERING_ASSUMPTION,
                source_document="CTA mission brief",
                source_location="INGECART portfolio specification",
                evidence_ids=[evidence.id],
                confidence=0.65,
                validation_status=ValidationStatus.UNVERIFIED,
            )
        )
        context.relate("client-ingecart", project.id, "HAS_PROJECT", evidence.id)
        if project.parent_project_id:
            context.relate(project.parent_project_id, project.id, "HAS_SUBPROJECT", evidence.id)
        projects.append(project)

    calls = []
    for raw_item in CATALOG_CALLS:
        item = dict(raw_item)
        verified = item.pop("official_verified", False)
        verification_date = date.fromisoformat(item.pop("verification_date"))
        call_evidence = context.save(
            FundingEvidence(
                id=f"evidence-{item['id']}", source_type=InformationLevel.ACTUAL,
                source_document=item["official_url"], source_location="Official programme page",
                source_text=f"Official funding card checked for {item['call_name']}",
                extraction_method="official_web_verification", official_source=True,
                evidence_ids=[evidence.id], validation_status=ValidationStatus.VERIFIED,
                verified_at=datetime.now(UTC), verified_by="CTA official-source review",
            )
        )
        call = context.save(
            FundingCall(
                **item,
                status=item["call_status"],
                source_type=InformationLevel.ACTUAL if verified else InformationLevel.ENGINEERING_ASSUMPTION,
                source_document=item["official_url"],
                source_location="Official programme page checked 2026-08-18",
                evidence_ids=[call_evidence.id], confidence=0.95 if verified else 0.35,
                verification_date=verification_date,
                validation_status=ValidationStatus.VERIFIED if verified else ValidationStatus.UNVERIFIED,
                verified_at=datetime.now(UTC) if verified else None,
            )
        )
        calls.append(call)

    matrix = []
    for project in projects:
        for call in calls:
            match = orchestrator.match(project.id, call.id)
            matrix.append({"project_id": project.id, "project_code": project.code, "call_id": call.id, **match})
            context.relate(project.id, call.id, "MATCHED_TO")

    missions = [
        context.save(
            FundingMission(
                id="mission-ingecart-source-document",
                objective="Ingest and verify INGECART primary project evidence",
                assigned_agent="EVIDENCE VERIFICATION AGENT",
                stage="VERIFY",
                next_action="Obtain original file, checksum it, extract page/section evidence, and requalify projects.",
                deliverable="Verified evidence package with page-level traceability",
                blocking_reason="Source document is not present",
                status="BLOCKED_INFORMATION_GAP",
                evidence_ids=[evidence.id],
                validation_status=ValidationStatus.MISSING_SOURCE,
            )
        )
    ]
    for call in calls:
        missions.append(
            context.save(
                FundingMission(
                    id=f"mission-verify-{call.id}",
                    objective=f"Verify current official requirements for {call.call_name}",
                    funding_call_id=call.id,
                    assigned_agent="FUNDING MONITORING AGENT",
                    stage="VERIFY",
                    next_action="Fetch official source, capture dates and requirements, then rerun matching.",
                    deliverable="Verified Funding Opportunity Card",
                    status="OPEN",
                    evidence_ids=[evidence.id],
                )
            )
        )

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "client": client.model_dump(mode="json"),
        "projects": [item.model_dump(mode="json") for item in projects],
        "funding_calls": [item.model_dump(mode="json") for item in calls],
        "matrix": matrix,
        "missions": [item.model_dump(mode="json") for item in missions],
        "scenarios": {project.id: funding_scenarios(project.preliminary_budget_eur or 0.0, None) for project in projects},
        "human_approval_gate": "AI ANALYSIS -> CONSULTANT REVIEW -> APPROVAL -> APPLICATION",
    }
    write_artifacts(payload)
    return payload


def write_artifacts(payload: dict[str, Any]) -> None:
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_ROOT.mkdir(parents=True, exist_ok=True)
    (KNOWLEDGE_ROOT / "ingecart_portfolio.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    matrix_lines = ["| Project | Funding call | Score | Decision |", "|---|---|---:|---|"]
    for row in payload["matrix"]:
        matrix_lines.append(f"| {row['project_code']} | {row['call_id']} | {row['score']} | {row['decision']} |")
    matrix = "\n".join(matrix_lines)
    opportunity_lines = [
        "| Territory | Status | Programme | Minimum | Grant | Loan | Maximum | Deadline |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    financial_lines = [
        "| Territory | Status | Programme | Budget fits EUR 60k | Grant | Repayable | Advance | Bridge need |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ]
    for call in payload.get("funding_calls", []):
        opportunity_lines.append(
            f"| {call['territory']} | {call['call_status']} | {call['call_name']} | "
            f"{call.get('budget_min_eur') or '-'} | {call.get('grant_rate_pct') or '-'}% | "
            f"{call.get('loan_rate_pct') or '-'}% | {call.get('max_aid_eur') or '-'} | "
            f"{call.get('closing_date') or 'Continuous / not stated'} |"
        )
        scenario = liquidity_scenario(60000, call)
        financial_lines.append(
            f"| {call['territory']} | {call['call_status']} | {call['call_name']} | "
            f"{'YES' if scenario['budget_eligible'] else 'NO'} | "
            f"{scenario['grant_eur']} | {scenario['loan_eur']} | {scenario['advance_eur']} | "
            f"{scenario['bridge_financing_need_eur']} |"
        )
    opportunities = "\n".join(opportunity_lines)
    financial = "\n".join(financial_lines)
    documentation = """# Application Dossier Checklist

1. Company eligibility: deeds, tax ID, SME status, IAE/industrial registration and tax/Social Security compliance.
2. Technical case: problem, state of art, uncertainty, hypothesis, TRL baseline/target, work packages, milestones and validation plan.
3. Economic case: itemised budget, staff hours and rates, supplier offers, financing plan, cash-flow forecast and annual accounts.
4. Evidence: dated specifications, architecture, tests, prototypes, invoices, bank payment records and page-level source traceability.
5. Compliance: incentive effect before project start where required, minimis declaration, other aid declarations, DNSH where applicable and no duplicate financing of the same cost.
6. Justification pack: time records, accounting ledger, invoices, payments, deliverables, test results, publicity obligations and auditor report where required.
"""
    reports = {
        "FUNDING_OPPORTUNITY_REPORT.md": "# Funding Opportunity Report\n\nOfficial-source catalogue checked on 2026-08-18.\n\n" + opportunities,
        "PROJECT_FUNDING_ASSESSMENT.md": "# Project Funding Assessment\n\n" + matrix,
        "RD_QUALIFICATION_REPORT.md": "# I+D Qualification Report\n\nCurrent classification: INSUFFICIENT EVIDENCE until the primary document is ingested and verified.",
        "FUNDING_STRATEGY_REPORT.md": "# Funding Strategy Report\n\nFor a Navarra execution at EUR 60,000, assess Empresa Digital A.1 first: up to 35% (EUR 21,000), but the work must be completed and paid before applying. CDTI PID is excluded below EUR 175,000. For a Catalonia execution, the open EU R&D&I coupon funds proposal preparation only, up to EUR 12,000; it does not fund engineering development or equipment.\n\nDo not enlarge a project solely to cross an aid threshold. Separate technical development, productive investment and proposal-preparation costs, and never allocate the same invoice twice.",
        "PROJECT_FUNDING_MATRIX.md": "# Project x Funding Matrix\n\n" + matrix,
        "FUNDING_FINANCIAL_SCENARIO.md": "# Funding Financial Scenario - EUR 60,000\n\n" + financial + "\n\nBridge need is the amount of awarded public support not received up front; own contribution remains a separate permanent funding requirement.",
        "APPLICATION_READINESS_REPORT.md": documentation,
        "FUNDING_CALENDAR.md": "# Funding Calendar\n\n- 2026-11-06: Navarra Empresa Digital 2026 closes. The project must already be completed and paid.\n- 2026-11-16: ACCIO European R&D&I coupon closes. Non-competitive while budget remains.\n- Continuous: CDTI PID, subject to EUR 175,000 minimum eligible budget.\n",
        "FUNDING_RISK_REPORT.md": "# Funding Risk Report\n\nHigh risks: primary INGECART source files still require ingestion; Navarra reimbursement creates pre-financing pressure; regional aid requires execution in that region; closed Catalonia calls are planning references only; CDTI is not eligible at EUR 60,000; and unsupported benchmark claims must not enter an application as facts.",
        "EXECUTIVE_FUNDING_DASHBOARD.md": "# Executive Funding Dashboard\n\n" + opportunities + "\n\n## Project x Funding\n\n" + matrix,
    }
    for filename, content in reports.items():
        (REPORT_ROOT / filename).write_text(content + "\n", encoding="utf-8")
    (REPORT_ROOT / "backlog.json").write_text(json.dumps(payload["missions"], indent=2, ensure_ascii=False), encoding="utf-8")
