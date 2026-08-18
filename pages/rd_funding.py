from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from backoffice.rd_funding.bootstrap import bootstrap_ingecart
from backoffice.rd_funding.context_service import FundingContextService
from backoffice.rd_funding.models import ClientProject
from backoffice.rd_funding.orchestrator import RDFundingOrchestrator


REPO_ROOT = Path(__file__).resolve().parent.parent


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def main() -> None:
    st.set_page_config(page_title="CTA R&D Funding", page_icon="💶", layout="wide")
    try:
        from backoffice.theme import inject_theme
        inject_theme()
    except Exception:
        pass

    context = FundingContextService()
    orchestrator = RDFundingOrchestrator(context)
    clients = context.list("CLIENT")
    projects = context.list("CLIENT_PROJECT")
    calls = context.list("FUNDING_CALL")
    missions = context.list("FUNDING_MISSION")

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
    metric_cols[5].metric("Potential funding", "Pending verification")

    dashboard, new_project, opportunities, evidence, missions_tab = st.tabs(
        ["INGECART Dashboard", "New Project", "Funding Radar", "Evidence", "Next Missions"]
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
                )
            )
            context.relate(client_id, project.id, "HAS_PROJECT")
            st.success(f"Project Discovery Card created: {project.code}")

    with opportunities:
        st.subheader("Funding Radar")
        if calls:
            st.dataframe(pd.DataFrame(calls)[["organisation", "program", "call_name", "official_url", "validation_status", "status"]], use_container_width=True, hide_index=True)
        st.warning("Discovery records cannot enter a final report until official-source verification is complete.")

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