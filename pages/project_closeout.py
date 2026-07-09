"""Streamlit page: Project Closeout / Cierre de Proyecto

Minimal, usable V1 implementing the requested tabs and basic persistence.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List

import streamlit as st

from services.project_closeout_service import ProjectCloseoutService
from services.project_closeout_extractor import extract_text_and_entities_from_file
from services.project_closeout_reporter import generate_project_closeout_report


def _render_master_data(project_id: str, project: Dict[str, Any], service: ProjectCloseoutService):
    st.markdown("#### Project Master Data")
    with st.form("master_data_form"):
        project_name = st.text_input("Project Name", value=project.get("project_name", ""))
        customer = st.text_input("Customer", value=project.get("master_data", {}).get("customer", ""))
        site = st.text_input("Site / Plant", value=project.get("master_data", {}).get("site", ""))
        country = st.text_input("Country", value=project.get("master_data", {}).get("country", ""))
        internal_pm = st.text_input("Internal Project Manager", value=project.get("master_data", {}).get("internal_pm", ""))
        technical_lead = st.text_input("Technical Lead", value=project.get("master_data", {}).get("technical_lead", ""))
        sales_owner = st.text_input("Sales Owner", value=project.get("master_data", {}).get("sales_owner", ""))
        start_date = st.text_input("Start Date (YYYY-MM-DD)", value=project.get("master_data", {}).get("start_date", ""))
        contract_signature = st.text_input("Contract Signature Date", value=project.get("master_data", {}).get("contract_signature_date", ""))
        planned_fat = st.text_input("Planned FAT Date", value=project.get("master_data", {}).get("planned_fat_date", ""))
        planned_shipment = st.text_input("Planned Shipment Date", value=project.get("master_data", {}).get("planned_shipment_date", ""))
        planned_install = st.text_input("Planned Installation Start", value=project.get("master_data", {}).get("planned_installation_start", ""))
        planned_sat = st.text_input("Planned SAT / Acceptance Date", value=project.get("master_data", {}).get("planned_sat_date", ""))
        closeout_date = st.text_input("Closeout Date", value=project.get("master_data", {}).get("closeout_date", ""))
        status = st.selectbox("Project Status", ["Open", "Execution", "SAT", "Closed", "On Hold"], index=0)
        description = st.text_area("Project description (executive)", value=project.get("master_data", {}).get("description", ""), height=140)

        submitted = st.form_submit_button("Save master data")
        if submitted:
            payload = project.get("master_data", {})
            payload.update({
                "project_name": project_name,
                "customer": customer,
                "site": site,
                "country": country,
                "internal_pm": internal_pm,
                "technical_lead": technical_lead,
                "sales_owner": sales_owner,
                "start_date": start_date,
                "contract_signature_date": contract_signature,
                "planned_fat_date": planned_fat,
                "planned_shipment_date": planned_shipment,
                "planned_installation_start": planned_install,
                "planned_sat_date": planned_sat,
                "closeout_date": closeout_date,
                "status": status,
                "description": description,
            })
            service.upsert_project(project_id, {"project_name": project_name, **payload})
            st.success("Master data saved.")


def _render_contracts_tab(project_id: str, project: Dict[str, Any], service: ProjectCloseoutService):
    st.markdown("#### Contract / Scope / Change Control")
    st.markdown("**Upload contract documents (PDF / DOCX / ZIP)**")
    uploaded = st.file_uploader("Upload contract files", accept_multiple_files=True, type=["pdf", "docx", "zip", "txt"] )
    if uploaded:
        for u in uploaded:
            meta = service.save_document(project_id, u, doc_type="contract")
            st.write(f"Saved {meta['filename']} -> {meta['path']}")
            # attempt quick extraction
            try:
                res = extract_text_and_entities_from_file(meta["path"])
                st.json(res["entities"])
            except Exception as e:
                st.warning(f"Extraction failed: {e}")

    st.markdown("---")
    st.markdown("#### Change Control Register")
    with st.form("change_control_form"):
        co_title = st.text_input("Title")
        co_date = st.text_input("Date (YYYY-MM-DD)")
        co_origin = st.selectbox("Origin", ["Customer", "Internal", "Supplier"]) 
        co_comm_impact = st.text_input("Commercial impact (EUR)")
        co_sched_impact = st.number_input("Schedule impact (days)", value=0)
        co_notes = st.text_area("Notes")
        add_co = st.form_submit_button("Add change order")
        if add_co:
            payload = {
                "title": co_title,
                "date": co_date,
                "origin": co_origin,
                "commercial_impact": float(co_comm_impact) if co_comm_impact else None,
                "schedule_impact_days": int(co_sched_impact),
                "notes": co_notes,
            }
            service.add_change_order(project_id, payload)
            st.success("Change order added.")

    cos = service.list_change_orders(project_id)
    if cos:
        st.write(f"{len(cos)} change orders")
        st.dataframe(cos)


def _render_engineering_tab(project_id: str, project: Dict[str, Any], service: ProjectCloseoutService):
    st.markdown("#### Engineering & Execution History")
    eng_text = st.text_area("Engineering summary / lessons learned", value=project.get("master_data", {}).get("engineering_summary", ""), height=200)
    if st.button("Save engineering summary"):
        md = project.get("master_data", {})
        md["engineering_summary"] = eng_text
        service.upsert_project(project_id, {"project_name": project.get("project_name", project_id), **md})
        st.success("Saved.")
    st.markdown("Upload engineering documents")
    upl = st.file_uploader("Engineering files", accept_multiple_files=True)
    if upl:
        for u in upl:
            meta = service.save_document(project_id, u, doc_type="engineering")
            st.write(meta["filename"])


def _render_installation_tab(project_id: str, project: Dict[str, Any], service: ProjectCloseoutService):
    st.markdown("#### Installation / Commissioning / SAT")
    st.write("Upload site reports, daily logs, photos, SAT reports.")
    upl = st.file_uploader("Installation files", accept_multiple_files=True, key="install_upload")
    if upl:
        for u in upl:
            meta = service.save_document(project_id, u, doc_type="installation")
            st.write(meta["filename"]) 


def _render_punchlist_tab(project_id: str, project: Dict[str, Any], service: ProjectCloseoutService):
    st.markdown("#### Punch List & Issues")
    st.markdown("Upload CSV or Excel punch lists and the system will try to parse them.")
    up = st.file_uploader("Punch list import (CSV/XLSX)", accept_multiple_files=False, type=["csv", "xlsx", "xls"]) 
    if up:
        res = service.import_issues_from_file(project_id, up, up.name)
        st.json(res)
    issues = service.get_issues_df(project_id)
    try:
        import pandas as pd

        if isinstance(issues, pd.DataFrame):
            st.dataframe(issues)
        else:
            st.dataframe(pd.DataFrame(issues))
    except Exception:
        st.write(issues)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Export issues CSV"):
            try:
                import pandas as pd

                df = service.get_issues_df(project_id)
                if not isinstance(df, pd.DataFrame):
                    df = pd.DataFrame(df)
                st.download_button("Download CSV", data=df.to_csv(index=False), file_name=f"{project_id}_issues.csv")
            except Exception as e:
                st.error(f"Export failed: {e}")


def _render_feedback_tab(project_id: str, project: Dict[str, Any], service: ProjectCloseoutService):
    st.markdown("#### Customer Feedback / Emails / Incidents")
    up = st.file_uploader("Upload communications (PDF / TXT / EML)", accept_multiple_files=True)
    if up:
        for u in up:
            meta = service.save_document(project_id, u, doc_type="feedback")
            st.write(meta["filename"]) 


def _render_financial_tab(project_id: str, project: Dict[str, Any], service: ProjectCloseoutService):
    st.markdown("#### Financial & Payment Milestones")
    st.info("V1 provides manual fields and file upload for financial documents.")
    up = st.file_uploader("Financial docs (invoices, certificates)", accept_multiple_files=True, key="fin_upload")
    if up:
        for u in up:
            meta = service.save_document(project_id, u, doc_type="financial")
            st.write(meta["filename"]) 


def _render_closeout_tab(project_id: str, project: Dict[str, Any], service: ProjectCloseoutService):
    st.markdown("#### Closeout Report & Gantt")
    if st.button("Generate closeout report (HTML + JSON)"):
        out = generate_project_closeout_report(service, project_id)
        st.success("Report generated")
        st.write(out)
        # show HTML inline if possible
        try:
            import streamlit.components.v1 as components
            with open(out["html"], "r", encoding="utf-8") as f:
                html = f.read()
            components.html(html, height=700, scrolling=True)
        except Exception:
            st.markdown(f"Report written to: {out['html']}")


def main():
    st.set_page_config(page_title="Project Closeout", layout="wide")
    service = ProjectCloseoutService()
    st.title("Project Closeout / Cierre de Proyecto")

    # Sidebar project selection
    with st.sidebar:
        st.header("Project Closeout")
        projects = service.list_projects()
        project_ids = [p["project_id"] for p in projects]
        selected = st.selectbox("Select project", ["<Create New>"] + project_ids)
        if selected == "<Create New>":
            new_id = st.text_input("Project ID")
            new_name = st.text_input("Project Name")
            if st.button("Create project"):
                if not new_id:
                    st.error("Project ID required")
                else:
                    service.upsert_project(new_id, {"project_name": new_name})
                    st.experimental_rerun()
        else:
            project_id = selected

    if selected == "<Create New>":
        st.info("Create a project from the sidebar to begin.")
        return

    project = service.get_project(project_id) or {"project_id": project_id, "project_name": project_id, "master_data": {}}

    tabs = st.tabs([
        "PROJECT MASTER DATA",
        "CONTRACT / SCOPE / CHANGE CONTROL",
        "ENGINEERING & EXECUTION HISTORY",
        "INSTALLATION / COMMISSIONING / SAT",
        "PUNCH LIST & ISSUES",
        "CUSTOMER FEEDBACK / EMAILS / INCIDENTS",
        "FINANCIAL & PAYMENT MILESTONES",
        "CLOSEOUT REPORT & GANTT",
    ])

    with tabs[0]:
        _render_master_data(project_id, project, service)
    with tabs[1]:
        _render_contracts_tab(project_id, project, service)
    with tabs[2]:
        _render_engineering_tab(project_id, project, service)
    with tabs[3]:
        _render_installation_tab(project_id, project, service)
    with tabs[4]:
        _render_punchlist_tab(project_id, project, service)
    with tabs[5]:
        _render_feedback_tab(project_id, project, service)
    with tabs[6]:
        _render_financial_tab(project_id, project, service)
    with tabs[7]:
        _render_closeout_tab(project_id, project, service)
