from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from backoffice.rd_funding.bootstrap import bootstrap_ingecart
from backoffice.rd_funding.context_service import FundingContextService
from backoffice.rd_funding.engines import liquidity_scenario
from backoffice.rd_funding.models import ClientProject
from backoffice.rd_funding.orchestrator import RDFundingOrchestrator
from backoffice.ui.components.consulting_brand import (
    CONSULTING_HTML_REPORT,
    CONSULTING_QUICKSTART,
    render_cta_brand_hero,
)


REPO_ROOT = Path(__file__).resolve().parent.parent


def _jump(page: str) -> None:
    st.switch_page(page)


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _money(value: float | int | None) -> str:
    return f"{float(value or 0):,.0f} EUR"


def main() -> None:
    st.set_page_config(page_title="CTA R&D Funding", page_icon="💶", layout="wide")
    try:
        from backoffice.theme import inject_theme
        inject_theme()
    except Exception:
        pass

    render_cta_brand_hero(
        "CTA R&D Funding Engine",
        "Calificacion de proyectos, radar de convocatorias y seguimiento de evidencias desde el nuevo eje ERP Profesional.",
        context_label="ERP Profesional > Reporting",
    )
    top_nav = st.columns(4)
    with top_nav[0]:
        if st.button("Hub ERP Profesional", use_container_width=True):
            _jump("pages/erp_profesional.py")
    with top_nav[1]:
        if st.button("Facturacion ERP", use_container_width=True):
            _jump("pages/facturacion.py")
    with top_nav[2]:
        if st.button("Consultoria Funding", use_container_width=True):
            _jump("pages/funding_consulting_center.py")
    with top_nav[3]:
        if CONSULTING_HTML_REPORT.exists() and CONSULTING_QUICKSTART.exists():
            st.caption("HTML y guia disponibles en el hub ERP.")

    context = FundingContextService()
    orchestrator = RDFundingOrchestrator(context)
    clients = context.list("CLIENT")
    projects = [item for item in context.list("CLIENT_PROJECT") if item.get("status") != "ARCHIVED"]
    calls = [item for item in context.list("FUNDING_CALL") if item.get("status") != "ARCHIVED"]
    missions = [item for item in context.list("FUNDING_MISSION") if item.get("status") != "ARCHIVED"]

    st.title("CTA INDUSTRIAL R&D FUNDING ENGINE")
    st.caption("Project discovery, qualification, funding strategy, dossier readiness and monitoring")
    if not projects:
        st.warning("INGECART workspace is not initialized.")
        if st.button("Initialize INGECART portfolio", type="primary"):
            bootstrap_ingecart(context)
            st.rerun()

    metric_cols = st.columns(6)
    metric_cols[0].metric("Active clients", len(clients))
    metric_cols[1].metric("Active projects", len(projects))
    metric_cols[2].metric("Opportunities", len(calls))
    metric_cols[3].metric("Verified calls", sum(item.get("validation_status") == "VERIFIED" for item in calls))
    metric_cols[4].metric("Open missions", sum(item.get("status") != "COMPLETED" for item in missions))
    open_calls = [item for item in calls if str(item.get("call_status", "")).startswith("OPEN")]
    metric_cols[5].metric("Open now", len(open_calls))

    dashboard, matrix_tab, new_project, opportunities, evidence, missions_tab = st.tabs(
        ["Mission Control", "Project x Funding", "New Project", "Funding Radar", "Evidence", "Next Missions"]
    )

    with dashboard:
        st.subheader("INGECART Funding Dashboard")
        rows = []
        for project in sorted(projects, key=lambda item: item.get("code", "")):
            matches = [orchestrator.match(project["id"], call["id"]) for call in calls]
            best = max(matches, key=lambda item: item["score"]) if matches else None
            qualification = orchestrator.qualify(project["id"])
            rows.append(
                {
                    "Project": project.get("code"),
                    "Name": project.get("name"),
                    "Status": project.get("status"),
                    "I+D classification": qualification["classification"],
                    "Best score": best["score"] if best else None,
                    "Decision": best["decision"] if best else "NO DATA",
                    "Readiness": "BLOCKED - EVIDENCE" if qualification["classification"] == "INSUFFICIENT EVIDENCE" else "REVIEW",
                    "Next action": "Verify project evidence and official call",
                    "Risk": "HIGH" if not calls else "MEDIUM",
                }
            )
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.info("No application can be submitted automatically. AI analysis requires consultant review and approval.")

    with matrix_tab:
        st.subheader("Project x Funding Matrix")
        matrix_rows = []
        for project in sorted(projects, key=lambda item: item.get("code", "")):
            for call in calls:
                match = orchestrator.match(project["id"], call["id"])
                matrix_rows.append(
                    {
                        "Project": project.get("code"),
                        "Region": project.get("execution_region") or "Pending",
                        "Funding": call.get("call_name"),
                        "Status": call.get("call_status"),
                        "Score": match["score"],
                        "Decision": match["decision"],
                        "Why": "; ".join(match["rationale"][2:5]),
                    }
                )
        st.dataframe(pd.DataFrame(matrix_rows), use_container_width=True, hide_index=True)
        st.caption("Closed calls and incompatible budget or territory are hard NO-GO gates, regardless of average score.")

    with new_project:
        st.subheader("New Project")
        with st.form("new_rd_project"):
            col_a, col_b = st.columns(2)
            with col_a:
                client_id = st.selectbox("Cliente", [item["id"] for item in clients] or ["client-ingecart"])
                code = st.text_input("Proyecto / código")
                name = st.text_input("Nombre")
                product = st.text_input("Producto")
                technology = st.text_input("Área tecnológica", placeholder="robotics, AI, automation")
                problem = st.text_area("Problema")
                current_state = st.text_area("Estado actual")
                target_state = st.text_area("Estado objetivo")
            with col_b:
                innovation = st.text_area("Innovación")
                uncertainties = st.text_area("Incertidumbres tecnológicas", placeholder="Separadas por comas")
                hypotheses = st.text_area("Hipótesis", placeholder="Separadas por comas")
                expected = st.text_area("Resultado esperado")
                market = st.text_input("Mercado", value="Industrial")
                trl = st.columns(2)
                initial_trl = trl[0].number_input("TRL inicial", 1, 9, 3)
                target_trl = trl[1].number_input("TRL objetivo", 1, 9, 6)
                duration = st.number_input("Duración (meses)", 1, 120, 24)
                budget = st.number_input("Presupuesto preliminar EUR", 0.0, step=10000.0)
                execution_region = st.selectbox("Región de ejecución", ["Navarra", "Cataluña", "Otra región de España"])
            submitted = st.form_submit_button("Create Project Discovery Card", type="primary")
        if submitted:
            project = context.save(
                ClientProject(
                    client_id=client_id, code=code, name=name, product=product,
                    technology_areas=_split(technology), problem=problem, current_state=current_state,
                    target_state=target_state, innovation=innovation,
                    technological_uncertainties=_split(uncertainties), hypotheses=_split(hypotheses),
                    expected_result=expected, market=market, initial_trl=initial_trl,
                    target_trl=target_trl, duration_months=duration, preliminary_budget_eur=budget,
                    execution_region=execution_region,
                )
            )
            context.relate(client_id, project.id, "HAS_PROJECT")
            st.success(f"Project Discovery Card created: {project.code}")

    with opportunities:
        st.subheader("Funding Radar")
        if calls:
            filter_cols = st.columns(3)
            territories = filter_cols[0].multiselect("Territory", sorted({item.get("territory", "") for item in calls}), default=[])
            statuses = filter_cols[1].multiselect("Call status", sorted({item.get("call_status", "UNKNOWN") for item in calls}), default=[])
            technology = filter_cols[2].text_input("Technology contains", placeholder="AI, automation, software...").lower().strip()
            filtered = [
                item for item in calls
                if (not territories or item.get("territory") in territories)
                and (not statuses or item.get("call_status") in statuses)
                and (not technology or technology in " ".join(item.get("technologies", [])).lower())
            ]
            radar_rows = [
                {
                    "Territory": item.get("territory"),
                    "Status": item.get("call_status"),
                    "Programme": item.get("call_name"),
                    "Minimum": _money(item.get("budget_min_eur")) if item.get("budget_min_eur") else "None stated",
                    "Grant %": item.get("grant_rate_pct"),
                    "Loan %": item.get("loan_rate_pct"),
                    "Maximum aid": _money(item.get("max_aid_eur")) if item.get("max_aid_eur") else "Instrument-specific",
                    "Deadline": item.get("closing_date") or "Continuous / not stated",
                    "Verified": item.get("validation_status"),
                }
                for item in filtered
            ]
            st.dataframe(pd.DataFrame(radar_rows), use_container_width=True, hide_index=True)

            if filtered:
                selected_id = st.selectbox(
                    "Analyse opportunity",
                    [item["id"] for item in filtered],
                    format_func=lambda call_id: next(item["call_name"] for item in filtered if item["id"] == call_id),
                )
                selected = next(item for item in filtered if item["id"] == selected_id)
                project_cost = st.number_input("Project cost for liquidity analysis", min_value=0.0, value=60000.0, step=5000.0)
                scenario = liquidity_scenario(project_cost, selected)
                finance_cols = st.columns(5)
                finance_cols[0].metric("Grant", _money(scenario["grant_eur"]))
                finance_cols[1].metric("Repayable", _money(scenario["loan_eur"]))
                finance_cols[2].metric("Advance", _money(scenario["advance_eur"]))
                finance_cols[3].metric("Own contribution", _money(scenario["own_contribution_eur"]))
                finance_cols[4].metric("Bridge need", _money(scenario["bridge_financing_need_eur"]))
                if not scenario["budget_eligible"]:
                    st.error("NO-GO at this budget: the project is outside the instrument's financial limits.")
                if selected.get("call_status") not in {"OPEN", "OPEN_CONTINUOUS"}:
                    st.warning("This edition is not open. Keep it as a planning reference, not an available cash source.")
                detail_a, detail_b = st.columns(2)
                with detail_a:
                    st.markdown("**Financial conditions**")
                    st.write(selected.get("payment_timing") or "Payment timing not stated")
                    st.write(selected.get("interest_description") or "No credit interest applies / not stated")
                    if selected.get("repayment_years"):
                        st.write(f"Repayment: {selected['repayment_years']} years; grace: {selected.get('grace_years')} years")
                    st.write(selected.get("liquidity_notes") or "No additional liquidity note")
                    st.link_button("Official source", selected["official_url"])
                with detail_b:
                    st.markdown("**Required dossier**")
                    for document in selected.get("required_documents", []):
                        st.write(f"- {document}")
                    st.markdown("**Eligible costs**")
                    for cost in selected.get("eligible_costs", []):
                        st.write(f"- {cost}")
        st.info("Only official-source verified records may enter a final client report. Amounts remain subject to the legal call text and consultant review.")

    with evidence:
        st.subheader("Evidence / Truth Layer")
        st.dataframe(pd.DataFrame(context.list("FUNDING_EVIDENCE")), use_container_width=True, hide_index=True)
        source_readme = REPO_ROOT / "knowledge_hub" / "rd_funding" / "source_documents" / "README.md"
        if source_readme.exists():
            st.markdown(source_readme.read_text(encoding="utf-8"))

    with missions_tab:
        st.subheader("Mission Manager")
        st.dataframe(pd.DataFrame(missions), use_container_width=True, hide_index=True)
        st.caption("Missions continue through DECISION -> ACTION -> DELIVERABLE; research alone is not completion.")


if __name__ == "__main__":
    main()