"""Reproducible first-client bootstrap and evidence-governed report generation."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .context_service import FundingContextService
from .engines import funding_scenarios
from .models import (
    ClientProject, FundingCall, FundingClient, FundingEvidence, FundingMission,
    InformationLevel, ValidationStatus,
)
from .orchestrator import RDFundingOrchestrator


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_ROOT = REPO_ROOT / "reports" / "rd_funding"
KNOWLEDGE_ROOT = REPO_ROOT / "knowledge_hub" / "rd_funding"


PROJECTS = (
    {
        "id": "ingecart-p01", "code": "P01", "name": "INGETRANS SOFTWARE & CONTROL",
        "product": "INGETRANS", "technology_areas": ["industrial software", "automation", "control"],
        "problem": "Control and integration of reel logistics equipment and one or two corrugators.",
        "innovation": "Integrated movement, identification, weighing and dual-reel transfer control.",
        "technological_uncertainties": ["Multi-equipment coordination under variable plant conditions"],
        "hypotheses": ["Context-aware control can improve robust reel-flow coordination"],
        "available_documents": ["PROYECTOS PARA GESTION AYUDAS Y RECURSOS INGENIERIA I+D (missing file)"],
    },
    {
        "id": "ingecart-p02", "code": "P02", "name": "NEXT GENERATION AMR PLATFORM",
        "product": "Industrial AMR platform", "technology_areas": ["robotics", "amr", "smart manufacturing"],
        "problem": "Create a reusable AMR platform for industrial material flows.",
        "innovation": "Navigation, safety, fleet management and factory integration platform.",
        "technological_uncertainties": ["Reliable localization in changing factories", "Safe heterogeneous fleet coordination"],
        "hypotheses": ["A modular platform can support multiple industrial load domains"],
    },
    {
        "id": "ingecart-p02a", "code": "P02A", "name": "AMR MULTI-LOAD CORRUGATED BOARD",
        "product": "AMR multi-load platform", "technology_areas": ["robotics", "amr", "intralogistics"],
        "problem": "Adapt AMR mechanics and control to different corrugated-board load capacities.",
        "innovation": "Configurable handling, safety and control across load envelopes.",
        "technological_uncertainties": ["Dynamic stability across load capacities"],
        "hypotheses": ["Adaptive control can preserve safety across configurable loads"],
        "parent_project_id": "ingecart-p02",
    },
    {
        "id": "ingecart-p02b", "code": "P02B", "name": "AMR FOLDING CARTON",
        "product": "Folding-carton AMR", "technology_areas": ["robotics", "amr", "industrial automation"],
        "problem": "Adapt the AMR platform to folding-carton flows and handling constraints.",
        "innovation": "Domain-specific handling, sensors, integration and pilot validation.",
        "technological_uncertainties": ["Reliable handling of folding-carton load formats"],
        "hypotheses": ["A dedicated end-effector can reduce handling variability"],
        "parent_project_id": "ingecart-p02",
    },
    {
        "id": "ingecart-p03", "code": "P03", "name": "AI ENTERPRISE OPERATING SYSTEM",
        "product": "Enterprise AI operating system", "technology_areas": ["ai", "software", "multi-agent systems"],
        "problem": "Coordinate finance, funding, projects, procurement, administration, sales and legal workflows.",
        "innovation": "Governed context, knowledge graph, memory and human-AI orchestration.",
        "technological_uncertainties": ["Reliable cross-agent context isolation", "Evidence-grounded autonomous planning"],
        "hypotheses": ["A governed context layer can reduce unsupported agent decisions"],
    },
)


CALLS = (
    {
        "id": "call-navarra-rd", "funding_id": "NAVARRA-RD-WATCH", "organisation": "Gobierno de Navarra",
        "program": "Ayudas a proyectos de I+D", "call_name": "Navarra I+D - verification pending",
        "official_url": "https://www.navarra.es/es/tramites/on/-/line/ayudas-para-proyectos-de-i-d",
        "territory": "Navarra", "technologies": ["robotics", "amr", "ai", "automation"],
    },
    {
        "id": "call-cdti-pid", "funding_id": "CDTI-PID-WATCH", "organisation": "CDTI",
        "program": "Proyectos de Investigación y Desarrollo", "call_name": "CDTI PID - verification pending",
        "official_url": "https://www.cdti.es/ayudas/proyectos-de-investigacion-y-desarrollo-pid",
        "territory": "Spain", "technologies": ["robotics", "industrial software", "ai", "automation"],
    },
    {
        "id": "call-eu-horizon", "funding_id": "EU-HORIZON-WATCH", "organisation": "European Commission",
        "program": "Horizon Europe", "call_name": "Horizon Europe topic search - topic verification pending",
        "official_url": "https://funding-tenders.ec.europa.eu/portal/screen/opportunities/topic-search",
        "territory": "European Union", "technologies": ["robotics", "smart manufacturing", "ai"],
    },
)


def bootstrap_ingecart(context: FundingContextService | None = None) -> dict[str, Any]:
    context = context or FundingContextService()
    orchestrator = RDFundingOrchestrator(context)
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
    for item in CALLS:
        call = context.save(
            FundingCall(
                **item,
                status="WATCH",
                source_type=InformationLevel.ENGINEERING_ASSUMPTION,
                source_document=item["official_url"],
                source_location="Official portal entry point; current call not yet verified",
                evidence_ids=[evidence.id],
                confidence=0.35,
                validation_status=ValidationStatus.UNVERIFIED,
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
    reports = {
        "FUNDING_OPPORTUNITY_REPORT.md": "# Funding Opportunity Report\n\nAll initial opportunities are WATCH pending official verification.\n\n" + matrix,
        "PROJECT_FUNDING_ASSESSMENT.md": "# Project Funding Assessment\n\n" + matrix,
        "RD_QUALIFICATION_REPORT.md": "# I+D Qualification Report\n\nCurrent classification: INSUFFICIENT EVIDENCE until the primary document is ingested and verified.",
        "FUNDING_STRATEGY_REPORT.md": "# Funding Strategy Report\n\nVerify Navarra, CDTI and Horizon instruments; then select non-overlapping eligible-cost scenarios with consultant approval.",
        "PROJECT_FUNDING_MATRIX.md": "# Project x Funding Matrix\n\n" + matrix,
        "FUNDING_FINANCIAL_SCENARIO.md": "# Funding Financial Scenario\n\nNo funding amount is published because project budgets and verified intensities are missing.",
        "APPLICATION_READINESS_REPORT.md": "# Application Readiness Report\n\nStatus: NOT READY. Official call requirements and primary project evidence are unverified.",
        "FUNDING_CALENDAR.md": "# Funding Calendar\n\nNo deadline alerts generated until official closing dates are verified.",
        "FUNDING_RISK_REPORT.md": "# Funding Risk Report\n\nHigh risks: missing primary evidence, unverified calls, unknown budgets, unknown compatibility and cash-flow dates.",
        "EXECUTIVE_FUNDING_DASHBOARD.md": "# Executive Funding Dashboard\n\n" + matrix,
    }
    for filename, content in reports.items():
        (REPORT_ROOT / filename).write_text(content + "\n", encoding="utf-8")
    (REPORT_ROOT / "backlog.json").write_text(json.dumps(payload["missions"], indent=2, ensure_ascii=False), encoding="utf-8")
