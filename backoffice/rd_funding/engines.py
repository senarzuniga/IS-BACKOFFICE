"""Deterministic qualification, matching, budget, compatibility and calendar engines."""
from __future__ import annotations

from datetime import date
from typing import Any


MATCH_DIMENSIONS = (
    "technology_fit", "rd_fit", "trl_fit", "company_eligibility", "geographical_eligibility",
    "budget_fit", "sector_fit", "timing_fit", "eligible_cost_fit", "strategic_fit", "partner_fit",
    "funding_intensity", "success_probability",
)

BUDGET_CATEGORIES = (
    "Personal interno", "Personal externo", "Ingeniería", "Software", "Hardware",
    "Prototipos", "Componentes", "Materiales", "Ensayos", "Laboratorios",
    "Centros tecnológicos", "Universidades", "Subcontratación", "Consultoría",
    "Equipamiento", "Viajes", "Otros costes elegibles",
)

DOSSIER_SECTIONS = (
    "Executive Summary", "Company", "Problem", "State of Art", "Technological Challenge",
    "Technological Uncertainty", "Innovation", "Objectives", "Work Packages", "Tasks",
    "Milestones", "Deliverables", "Methodology", "Team", "Partners", "Budget",
    "Eligible Costs", "Funding Structure", "Risk", "Impact", "Market", "Exploitation",
    "IP", "Environmental Impact", "Timeline", "KPIs",
)


def design_project(project: dict[str, Any]) -> dict[str, Any]:
    """Propose an editable engineering structure; consultant approval remains mandatory."""
    areas = " ".join(project.get("technology_areas", [])).lower()
    technical = "AMR platform engineering" if any(term in areas for term in ("robot", "amr")) else "System architecture and engineering"
    return {
        "approval_status": "AI_PROPOSAL_REQUIRES_CONSULTANT_REVIEW",
        "work_packages": [
            {"code": "WP1", "name": "State of art and requirements", "tasks": ["Evidence review", "Baseline definition"], "milestone": "Requirements approved", "deliverable": "Technical baseline"},
            {"code": "WP2", "name": technical, "tasks": ["Architecture", "Prototype implementation"], "milestone": "Prototype ready", "deliverable": "Prototype and design dossier"},
            {"code": "WP3", "name": "Industrial validation", "tasks": ["Test protocol", "Pilot execution"], "milestone": "Validation complete", "deliverable": "Validation report"},
            {"code": "WP4", "name": "Exploitation and knowledge", "tasks": ["IP review", "Market plan"], "milestone": "Exploitation approved", "deliverable": "Exploitation plan"},
        ],
        "risks": ["Technical uncertainty not retired", "Pilot evidence incomplete", "Funding timing mismatch"],
        "dossier_sections": list(DOSSIER_SECTIONS),
    }


def qualify_project(project: dict[str, Any], evidence: list[dict[str, Any]]) -> dict[str, Any]:
    verified = [item for item in evidence if item.get("validation_status") == "VERIFIED"]
    uncertainty = len(project.get("technological_uncertainties", []))
    hypotheses = len(project.get("hypotheses", []))
    trl_delta = max(0, (project.get("target_trl") or 0) - (project.get("initial_trl") or 0))
    if not verified:
        classification = "INSUFFICIENT EVIDENCE"
    elif uncertainty >= 2 and hypotheses and trl_delta >= 2:
        classification = "I+D LIKELY"
    elif uncertainty or hypotheses:
        classification = "I+D POSSIBLE"
    elif any(term in " ".join(project.get("technology_areas", [])).lower() for term in ("ai", "software", "digital")):
        classification = "DIGITALISATION"
    else:
        classification = "INNOVATION"
    return {
        "classification": classification,
        "evidence_ids": [item["id"] for item in verified],
        "rationale": [
            f"Verified evidence records: {len(verified)}",
            f"Technological uncertainties: {uncertainty}",
            f"Testable hypotheses: {hypotheses}",
            f"TRL delta: {trl_delta}",
        ],
    }


def score_project_call(project: dict[str, Any], call: dict[str, Any]) -> dict[str, Any]:
    project_tech = {value.lower() for value in project.get("technology_areas", [])}
    call_tech = {value.lower() for value in call.get("technologies", [])}
    overlap = len(project_tech & call_tech)
    technology_fit = min(100.0, 35.0 + overlap * 25.0)
    territory = str(call.get("territory", "")).strip().lower()
    project_region = str(project.get("execution_region", "")).strip().lower()
    national_territories = {"spain", "españa", "european union", "eu"}
    if territory in national_territories:
        geography = 90.0
    elif not project_region:
        geography = 45.0
    else:
        geography = 95.0 if territory == project_region else 0.0
    project_budget = project.get("preliminary_budget_eur")
    minimum = call.get("budget_min_eur")
    maximum = call.get("budget_max_eur")
    budget_fit = 50.0 if project_budget is None else 85.0
    if project_budget is not None and minimum is not None and project_budget < minimum:
        budget_fit = 20.0
    if project_budget is not None and maximum is not None and project_budget > maximum:
        budget_fit = 30.0
    timing = 75.0 if call.get("closing_date") else 35.0
    verified = call.get("validation_status") == "VERIFIED"
    dimensions = {
        "technology_fit": technology_fit,
        "rd_fit": 75.0 if project.get("technological_uncertainties") else 45.0,
        "trl_fit": 70.0 if project.get("initial_trl") else 45.0,
        "company_eligibility": 55.0,
        "geographical_eligibility": geography,
        "budget_fit": budget_fit,
        "sector_fit": 70.0,
        "timing_fit": timing,
        "eligible_cost_fit": 65.0 if call.get("eligible_costs") else 35.0,
        "strategic_fit": 75.0,
        "partner_fit": 55.0,
        "funding_intensity": min(100.0, float(call.get("funding_rate_pct") or 40.0) * 1.5),
        "success_probability": 55.0 if verified else 25.0,
    }
    score = round(sum(dimensions.values()) / len(MATCH_DIMENSIONS), 2)
    call_status = str(call.get("call_status", "UNKNOWN")).upper()
    budget_blocked = budget_fit <= 30.0
    geography_blocked = geography == 0.0
    closed = call_status in {"CLOSED", "EXPIRED", "ARCHIVED"}
    if not verified:
        decision = "WATCH"
    elif closed or budget_blocked or geography_blocked:
        decision = "NO-GO"
    elif score >= 70:
        decision = "GO"
    elif score >= 50:
        decision = "STRATEGIC REDESIGN"
    else:
        decision = "NO-GO"
    return {
        "dimensions": dimensions,
        "score": score,
        "decision": decision,
        "rationale": [
            f"Technology overlap: {overlap}",
            "Official call data verified" if verified else "Call requires official-source verification",
            f"Call status: {call_status}",
            "Project budget outside instrument limits" if budget_blocked else "Project budget within known limits",
            "Execution territory is incompatible" if geography_blocked else "Execution territory is compatible or pending detail",
            "Human approval required before application",
        ],
    }


def assess_compatibility(calls: list[dict[str, Any]], cost_ids: list[str]) -> dict[str, Any]:
    if any(call.get("validation_status") != "VERIFIED" for call in calls):
        return {"result": "REQUIRES LEGAL/ADMINISTRATIVE REVIEW", "rationale": ["At least one call is unverified"]}
    if len(cost_ids) != len(set(cost_ids)):
        return {"result": "NOT COMPATIBLE", "rationale": ["The same eligible cost is allocated more than once"]}
    if any(call.get("minimis") is None for call in calls):
        return {"result": "POTENTIALLY COMPATIBLE", "rationale": ["Minimis status requires confirmation"]}
    return {"result": "COMPATIBLE", "rationale": ["No duplicate cost allocation detected"]}


def funding_scenarios(project_cost: float, funding_rate_pct: float | None) -> list[dict[str, Any]]:
    base_rate = max(0.0, min(float(funding_rate_pct or 0.0), 100.0)) / 100.0
    scenarios = []
    for name, factor in (("CONSERVATIVE", 0.7), ("BASE", 1.0), ("OPTIMISTIC", 1.15)):
        effective_rate = min(base_rate * factor, 1.0)
        public = round(project_cost * effective_rate, 2)
        scenarios.append(
            {
                "name": name,
                "project_cost_eur": project_cost,
                "potential_public_funding_eur": public,
                "client_contribution_eur": round(project_cost - public, 2),
                "effective_funding_pct": round(effective_rate * 100, 2),
                "estimated_payment_date": None,
                "financial_risk": "HIGH" if effective_rate == 0 or name == "OPTIMISTIC" else "MEDIUM",
            }
        )
    return scenarios


def liquidity_scenario(project_cost: float, call: dict[str, Any]) -> dict[str, Any]:
    """Estimate funding mix and pre-financing need without inventing payment terms."""
    minimum = call.get("budget_min_eur")
    maximum = call.get("budget_max_eur")
    budget_eligible = not ((minimum is not None and project_cost < minimum) or (maximum is not None and project_cost > maximum))
    grant_rate = float(call.get("grant_rate_pct") or 0.0) / 100.0
    loan_rate = float(call.get("loan_rate_pct") or 0.0) / 100.0
    non_repayable_rate = float(call.get("non_repayable_rate_pct") or 0.0) / 100.0
    advance_rate = float(call.get("advance_rate_pct") or 0.0) / 100.0
    if budget_eligible and non_repayable_rate and loan_rate:
        partially_repayable_aid = project_cost * loan_rate
        grant = partially_repayable_aid * non_repayable_rate
        loan = partially_repayable_aid - grant
    else:
        grant = min(project_cost * grant_rate, float(call.get("max_aid_eur") or project_cost)) if budget_eligible else 0.0
        loan = min(project_cost * loan_rate, max(0.0, project_cost - grant)) if budget_eligible else 0.0
    public_total = min(project_cost, grant + loan)
    advance = min(public_total, public_total * advance_rate)
    own_contribution = max(0.0, project_cost - public_total)
    bridge_need = max(0.0, project_cost - own_contribution - advance)
    return {
        "budget_eligible": budget_eligible,
        "project_cost_eur": round(project_cost, 2),
        "grant_eur": round(grant, 2),
        "loan_eur": round(loan, 2),
        "public_funding_eur": round(public_total, 2),
        "advance_eur": round(advance, 2),
        "own_contribution_eur": round(own_contribution, 2),
        "bridge_financing_need_eur": round(bridge_need, 2),
        "payment_timing": call.get("payment_timing") or "UNKNOWN",
        "advance_requires_guarantee": call.get("advance_requires_guarantee"),
        "interest_description": call.get("interest_description"),
        "repayment_years": call.get("repayment_years"),
        "grace_years": call.get("grace_years"),
        "warning": None if budget_eligible else "Project budget is outside the instrument limits",
    }


def deadline_alerts(closing_date: date | None, today: date | None = None) -> list[dict[str, Any]]:
    if closing_date is None:
        return []
    remaining = (closing_date - (today or date.today())).days
    thresholds = [180, 120, 90, 60, 30, 15, 7, 0]
    return [{"days": days, "due": remaining <= days, "remaining_days": remaining} for days in thresholds]
