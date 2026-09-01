from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
import streamlit as st

from backoffice.rd_funding.bootstrap import bootstrap_ingecart
from backoffice.rd_funding.context_service import FundingContextService
from backoffice.rd_funding.engines import (
    build_document_checklist,
    company_classification,
    create_alert_mission,
    generate_funding_alerts,
)
from backoffice.rd_funding.models import FundingMission
from backoffice.ui.components.consulting_brand import render_cta_brand_hero

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORTS_ROOT = REPO_ROOT / "reports" / "rd_funding"
KNOWLEDGE_ROOT = REPO_ROOT / "knowledge_hub" / "rd_funding"


def _jump(page: str) -> None:
    st.switch_page(page)


def _money(value: float | int | None) -> str:
    return f"{float(value or 0):,.0f} EUR"


def _parse_date(raw: Any) -> date | None:
    if raw is None:
        return None
    if isinstance(raw, date):
        return raw
    if isinstance(raw, str):
        try:
            return datetime.fromisoformat(raw).date()
        except ValueError:
            return None
    return None


def _status_bucket(call: dict[str, Any], today: date, horizon_days: int = 180) -> str:
    status = str(call.get("call_status", "UNKNOWN")).upper()
    opening = _parse_date(call.get("opening_date"))
    closing = _parse_date(call.get("closing_date"))
    remaining = (closing - today).days if closing else None
    if status in {"OPEN", "OPEN_CONTINUOUS"}:
        if remaining is not None and remaining <= 30:
            return "CLOSING SOON"
        return "OPEN NOW"
    if opening is not None:
        days_to_open = (opening - today).days
        if 0 <= days_to_open <= horizon_days:
            return "OPENING SOON"
    if status in {"CLOSED", "EXPIRED", "ARCHIVED"}:
        return "CLOSED"
    return "WATCH"


def _report_text(
    report_type: str,
    company: dict[str, Any] | None,
    projects: list[dict[str, Any]],
    alerts: list[dict[str, Any]],
) -> str:
    company_name = (company or {}).get("name", "N/A")
    lines = [
        f"# {report_type}",
        "",
        f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
        f"Company: {company_name}",
        f"Projects analysed: {len(projects)}",
        f"Opportunities analysed: {len(alerts)}",
        "",
        "## Top opportunities",
    ]
    for row in alerts[:10]:
        lines.append(
            f"- {row['name']} | {row['severity']} | Match {row['match_score']}/100 | "
            f"Status {row['status']} | Deadline {row['deadline'] or 'N/A'}"
        )
    if len(alerts) == 0:
        lines.append("- No opportunities available for current filters.")
    lines.extend(
        [
            "",
            "## Governance notes",
            "- Recommendations are decision support only.",
            "- Final eligibility and submission require consultant approval.",
            "- A call is prioritised only when official-source verification is present.",
        ]
    )
    return "\n".join(lines)


def _select_company(clients: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
    if not clients:
        return None
    selected_id = st.selectbox(
        "Empresa",
        options=[item["id"] for item in clients],
        format_func=lambda cid: next((x.get("name", cid) for x in clients if x["id"] == cid), cid),
        key=key,
    )
    return next(item for item in clients if item["id"] == selected_id)


def _projects_for_company(projects: list[dict[str, Any]], company: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not company:
        return []
    return [item for item in projects if item.get("client_id") == company.get("id") and item.get("status") != "ARCHIVED"]


def main() -> None:
    st.set_page_config(page_title="Funding Consulting Center", page_icon="🧭", layout="wide")
    try:
        from backoffice.theme import inject_theme

        inject_theme()
    except Exception:
        pass

    render_cta_brand_hero(
        "Funding Consulting Center",
        "Operacion consultiva para detectar oportunidades, estructurar evidencia y convertir el pipeline en proyectos financiables.",
        context_label="ERP Profesional > Reporting",
    )
    nav_cols = st.columns(3)
    with nav_cols[0]:
        if st.button("Hub ERP Profesional", use_container_width=True):
            _jump("pages/erp_profesional.py")
    with nav_cols[1]:
        if st.button("Facturacion ERP", use_container_width=True):
            _jump("pages/facturacion.py")
    with nav_cols[2]:
        if st.button("CTA R&D Funding Engine", use_container_width=True):
            _jump("pages/rd_funding.py")

    context = FundingContextService()
    clients = [item for item in context.list("CLIENT") if item.get("status") != "ARCHIVED"]
    projects = [item for item in context.list("CLIENT_PROJECT") if item.get("status") != "ARCHIVED"]
    calls = [item for item in context.list("FUNDING_CALL") if item.get("status") != "ARCHIVED"]
    missions = [item for item in context.list("FUNDING_MISSION") if item.get("status") != "ARCHIVED"]
    evidence = [item for item in context.list("FUNDING_EVIDENCE") if item.get("status") != "ARCHIVED"]

    st.title("R&D FUNDING CONSULTING CENTER")
    st.caption("Panel operativo de consultoría para detectar, priorizar, documentar y ejecutar ayudas sin salir de IS-BACKOFFICE.")

    if not clients or not projects or not calls:
        st.warning("Workspace de funding incompleto. Inicializa la cartera base para operar.")
        if st.button("Inicializar cartera INGECART", type="primary"):
            bootstrap_ingecart(context)
            st.rerun()

    top = st.columns(6)
    top[0].metric("Empresas", len(clients))
    top[1].metric("Proyectos", len(projects))
    top[2].metric("Ayudas catalogadas", len(calls))
    top[3].metric("Ayudas verificadas", sum(item.get("validation_status") == "VERIFIED" for item in calls))
    top[4].metric("Misiones abiertas", sum(item.get("status") != "COMPLETED" for item in missions))
    top[5].metric("Evidencias", len(evidence))

    tab_open, tab_manage, tab_knowledge, tab_reports, tab_analysis = st.tabs(
        [
            "Ayudas Abiertas",
            "Gestión de Ayudas",
            "Archivo de conocimiento y documentación",
            "Generador de informes",
            "Análisis ayudas vs empresas",
        ]
    )

    with tab_open:
        st.subheader("Ayudas existentes y próximas (horizonte 6 meses)")
        today = date.today()
        filters = st.columns(4)
        selected_company = _select_company(clients, key="open_company")
        company_projects = _projects_for_company(projects, selected_company)
        project_options = ["(Todos los proyectos)"] + [f"{p.get('code', 'N/A')} - {p.get('name', p['id'])}" for p in company_projects]
        project_label = filters[0].selectbox("Proyecto", options=project_options, index=0)
        selected_project = None
        if project_label != "(Todos los proyectos)":
            selected_project = next(item for item in company_projects if f"{item.get('code', 'N/A')} - {item.get('name', item['id'])}" == project_label)
        profile_filter = filters[1].multiselect(
            "Filtro por perfil",
            ["INDUSTRIAL COMPANIES", "NEW COMPANIES NAVARRA", "AUTONOMOUS", "WOMEN ENTREPRENEURS", "R&D / INNOVATION", "DIGITAL / AI", "INVESTMENT", "EMPLOYMENT", "EUROPE"],
            default=[],
        )
        state_filter = filters[2].multiselect("Estado temporal", ["OPEN NOW", "OPENING SOON", "CLOSING SOON"], default=["OPEN NOW", "OPENING SOON", "CLOSING SOON"])
        only_verified = filters[3].toggle("Solo VERIFIED MATCH", value=False)

        alert_rows: list[dict[str, Any]] = []
        source_alerts = generate_funding_alerts(company=selected_company, project=selected_project, calls=calls)
        categories = company_classification(selected_company or {})
        for alert in source_alerts:
            call = next((item for item in calls if item.get("id") == alert.get("id")), None)
            if not call:
                continue
            bucket = _status_bucket(call, today, horizon_days=180)
            if bucket not in state_filter:
                continue
            if only_verified and alert.get("alert_state") != "VERIFIED MATCH":
                continue
            territory = str(call.get("territory", "")).lower()
            matched_profile = True
            if profile_filter:
                matched_profile = False
                if "INDUSTRIAL COMPANIES" in profile_filter and "INDUSTRIAL COMPANY" in categories:
                    matched_profile = True
                if "NEW COMPANIES NAVARRA" in profile_filter and "NEW COMPANY" in categories and "navarra" in territory:
                    matched_profile = True
                if "AUTONOMOUS" in profile_filter and "AUTONOMOUS" in categories:
                    matched_profile = True
                if "WOMEN ENTREPRENEURS" in profile_filter and "WOMAN ENTREPRENEUR" in categories:
                    matched_profile = True
                if "R&D / INNOVATION" in profile_filter and any(term in " ".join(call.get("technologies", [])).lower() for term in ("r&d", "i+d", "innovation")):
                    matched_profile = True
                if "DIGITAL / AI" in profile_filter and any(term in " ".join(call.get("technologies", [])).lower() for term in ("ai", "digital", "software", "automation")):
                    matched_profile = True
                if "INVESTMENT" in profile_filter and call.get("budget_min_eur") is not None:
                    matched_profile = True
                if "EMPLOYMENT" in profile_filter and any("personal" in term.lower() for term in call.get("eligible_costs", [])):
                    matched_profile = True
                if "EUROPE" in profile_filter and any(term in territory for term in ("europe", "eu")):
                    matched_profile = True
            if not matched_profile:
                continue
            alert_rows.append(
                {
                    "Prioridad": alert.get("severity"),
                    "Estado temporal": bucket,
                    "Convocatoria": alert.get("name"),
                    "Organismo": alert.get("organism"),
                    "Estado": alert.get("status"),
                    "Match": f"{alert.get('match_score')}/100",
                    "Deadline": alert.get("deadline") or "N/A",
                    "Eligibility": alert.get("eligibility"),
                    "Acción recomendada": alert.get("recommended_action"),
                    "Potencial máx.": _money(call.get("max_aid_eur")),
                    "Fuente oficial": call.get("official_url"),
                }
            )

        st.dataframe(pd.DataFrame(alert_rows), use_container_width=True, hide_index=True)
        st.caption("Incluye ayudas abiertas hoy y aperturas previstas en los próximos 180 días (6 meses).")
        if alert_rows:
            st.markdown("#### Tarjetas de oportunidad")
            for idx, row in enumerate(alert_rows[:8], start=1):
                with st.expander(f"[{row['Prioridad']}] {row['Convocatoria']} - {row['Estado temporal']}", expanded=(idx == 1)):
                    st.write(f"**Organismo:** {row['Organismo']}")
                    st.write(f"**Match:** {row['Match']} | **Estado:** {row['Estado']} | **Deadline:** {row['Deadline']}")
                    st.write(f"**Eligibility:** {row['Eligibility']}")
                    st.write(f"**Potential funding:** {row['Potencial máx.']}")
                    st.link_button("Ver convocatoria oficial", row["Fuente oficial"])

    with tab_manage:
        st.subheader("Gestión documental y de proceso por ayuda")
        selected_company = _select_company(clients, key="manage_company")
        company_projects = _projects_for_company(projects, selected_company)
        project_id = st.selectbox(
            "Proyecto de trabajo",
            options=[item["id"] for item in company_projects] if company_projects else [],
            format_func=lambda pid: next((f"{x.get('code', '')} - {x.get('name', pid)}" for x in company_projects if x["id"] == pid), pid),
        )
        selected_project = next((item for item in company_projects if item["id"] == project_id), None)
        call_id = st.selectbox(
            "Ayuda a gestionar",
            options=[item["id"] for item in calls] if calls else [],
            format_func=lambda cid: next((f"{x.get('call_name', cid)} ({x.get('call_status', 'UNKNOWN')})" for x in calls if x["id"] == cid), cid),
        )
        selected_call = next((item for item in calls if item["id"] == call_id), None)

        checklist = build_document_checklist(company=selected_company, project=selected_project, call=selected_call)
        checklist_rows = [{"Sección": key, "Estado": value} for key, value in checklist["sections"].items()]
        st.dataframe(pd.DataFrame(checklist_rows), use_container_width=True, hide_index=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Application Readiness", f"{int(checklist['application_readiness_pct'])}%")
        c2.metric("Secciones pendientes", len(checklist["missing_sections"]))
        c3.metric("Requieren revisión", len(checklist["requires_review"]))

        st.markdown("#### Flujo operativo")
        stages = [
            "Diagnóstico",
            "Propuesta",
            "Documentación",
            "Solicitud",
            "Resolución",
            "Ejecución",
            "Justificación",
            "Seguimiento",
        ]
        process_rows = [{"Fase": stage, "Estado": "OPEN" if idx < 3 else "PENDING"} for idx, stage in enumerate(stages)]
        st.dataframe(pd.DataFrame(process_rows), use_container_width=True, hide_index=True)

        if st.button("Crear misión desde esta ayuda", type="primary"):
            if not selected_call:
                st.error("Selecciona una ayuda para crear la misión.")
            else:
                alert = generate_funding_alerts(company=selected_company, project=selected_project, calls=[selected_call])[0]
                mission_payload = create_alert_mission(alert=alert, project_id=project_id, call_id=call_id)
                mission = context.save(
                    FundingMission(
                        id=f"mission-{uuid4()}",
                        objective=mission_payload["objective"],
                        project_id=mission_payload["project_id"],
                        funding_call_id=mission_payload["funding_call_id"],
                        assigned_agent=mission_payload["assigned_agent"],
                        stage=mission_payload["stage"],
                        next_action=mission_payload["next_action"],
                        deliverable=mission_payload["deliverable"],
                        blocking_reason=mission_payload["blocking_reason"],
                        status="OPEN",
                    )
                )
                st.success(f"Misión creada: {mission.id}")

    with tab_knowledge:
        st.subheader("Archivo de conocimiento y documentación")
        left, right = st.columns(2)
        with left:
            st.markdown("**Evidence Layer (Funding Evidence)**")
            st.dataframe(pd.DataFrame(evidence), use_container_width=True, hide_index=True)
        with right:
            st.markdown("**Knowledge Hub / Report Files**")
            files = []
            for root in (KNOWLEDGE_ROOT, REPORTS_ROOT):
                if root.exists():
                    for item in sorted(root.glob("*")):
                        files.append(
                            {
                                "Ruta": str(item.relative_to(REPO_ROOT)),
                                "Tipo": "Carpeta" if item.is_dir() else "Archivo",
                                "Tamaño bytes": item.stat().st_size if item.is_file() else 0,
                                "Modificado": datetime.fromtimestamp(item.stat().st_mtime).isoformat(timespec="seconds"),
                            }
                        )
            st.dataframe(pd.DataFrame(files), use_container_width=True, hide_index=True)

    with tab_reports:
        st.subheader("Generador de informes")
        report_type = st.selectbox(
            "Tipo de informe",
            [
                "DAILY FUNDING ALERT REPORT",
                "WEEKLY FUNDING OPPORTUNITY REPORT",
                "CLIENT FUNDING REPORT",
                "PROJECT FUNDING REPORT",
                "NEW COMPANY FUNDING REPORT",
                "AUTONOMOUS FUNDING REPORT",
                "WOMEN ENTREPRENEUR FUNDING REPORT",
                "CLOSING DEADLINES REPORT",
                "FUNDING STRATEGY REPORT",
            ],
        )
        selected_company = _select_company(clients, key="report_company")
        company_projects = _projects_for_company(projects, selected_company)
        project_for_report = company_projects[0] if company_projects else None
        alerts = generate_funding_alerts(company=selected_company, project=project_for_report, calls=calls)
        report_md = _report_text(report_type, selected_company, company_projects, alerts)
        st.markdown(report_md)
        if st.button("Guardar informe en reports/rd_funding", type="primary"):
            REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
            safe_type = report_type.lower().replace(" ", "_").replace("/", "_")
            target = REPORTS_ROOT / f"{safe_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            target.write_text(report_md, encoding="utf-8")
            st.success(f"Informe guardado: {target.relative_to(REPO_ROOT)}")
        st.download_button("Descargar informe", data=report_md.encode("utf-8"), file_name="funding_report.md", mime="text/markdown")

    with tab_analysis:
        st.subheader("Herramienta de análisis de ayudas vs empresas")
        rows: list[dict[str, Any]] = []
        for company in clients:
            company_projects = _projects_for_company(projects, company)
            categories = company_classification(company)
            if not company_projects:
                continue
            for call in calls:
                alerts = generate_funding_alerts(company=company, project=company_projects[0], calls=[call])
                if not alerts:
                    continue
                alert = alerts[0]
                rows.append(
                    {
                        "Empresa": company.get("name", company["id"]),
                        "Categorías": ", ".join(categories),
                        "Proyecto base": f"{company_projects[0].get('code', '')} - {company_projects[0].get('name', '')}",
                        "Convocatoria": call.get("call_name"),
                        "Territorio": call.get("territory"),
                        "Estado": call.get("call_status"),
                        "Match": alert.get("match_score"),
                        "Severidad": alert.get("severity"),
                        "Elegibilidad": alert.get("eligibility"),
                        "Acción": alert.get("recommended_action"),
                    }
                )
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
        if not df.empty:
            st.markdown("#### Top oportunidades por empresa")
            top_rows = (
                df.sort_values(["Empresa", "Match"], ascending=[True, False])
                .groupby("Empresa", as_index=False)
                .head(3)
                .reset_index(drop=True)
            )
            st.dataframe(top_rows, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
