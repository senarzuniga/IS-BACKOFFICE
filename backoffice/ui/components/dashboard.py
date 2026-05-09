from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

_COMMAND_SUGGESTIONS = [
    "Show risky accounts",
    "Analyze Q2 revenue drop",
    "Summarize latest client communications",
    "Find pricing anomalies",
    "Which opportunities may close this month?",
]


def _render_workspace_cards() -> None:
    workspaces = [
        ("Clients & Accounts", "18 cuentas prioritarias", "3 cuentas sin respuesta >14 días"),
        ("Deals & Pipeline", "€4.8M pipeline activo", "2 oportunidades críticas este mes"),
        ("Research & Documents", "126 documentos trazados", "6 briefs listos para revisión"),
        ("AI Agents", "7 agentes disponibles", "1 agente pendiente de supervisión"),
    ]
    cols = st.columns(len(workspaces))
    for idx, (title, summary, detail) in enumerate(workspaces):
        with cols[idx]:
            st.markdown(f"**{title}**")
            st.caption(summary)
            st.info(detail)


def _classify_command(command: str) -> dict[str, Any]:
    lowered = command.lower()
    if any(term in lowered for term in ("risk", "riesg", "alert")):
        return {
            "workspace": "Alerts & Risks",
            "intent": "Risk monitoring",
            "summary": "Priority risk review routed to the risk workspace.",
            "findings": [
                "3 cuentas estratégicas muestran caída de actividad.",
                "2 ofertas llevan más de 21 días congeladas.",
                "1 anomalía de pricing requiere validación comercial.",
            ],
            "actions": ["Open risky accounts", "Review stalled deals", "Trigger follow-up email"],
        }
    if any(term in lowered for term in ("pipeline", "opportun", "close", "pricing", "revenue")):
        return {
            "workspace": "Deals & Pipeline",
            "intent": "Pipeline analysis",
            "summary": "Commercial pipeline review prepared for the deals workspace.",
            "findings": [
                "La cobertura de pipeline es 3.1x el objetivo mensual.",
                "2 oportunidades suben de probabilidad por nueva actividad.",
                "El descuento medio en propuestas críticas está por encima del rango objetivo.",
            ],
            "actions": ["Inspect top opportunities", "Validate pricing bands", "Generate executive forecast"],
        }
    if any(term in lowered for term in ("document", "research", "summarize", "communication")):
        return {
            "workspace": "Research & Documents",
            "intent": "Research synthesis",
            "summary": "Document intelligence workspace prepared with traceable sources.",
            "findings": [
                "Los últimos correos del cliente concentran peticiones sobre pricing.",
                "Hay 4 documentos clave con contenido coincidente.",
                "El resumen ejecutivo está listo para publicación.",
            ],
            "actions": ["Open document workspace", "Run executive summary", "Inspect source evidence"],
        }
    return {
        "workspace": "Intelligence Center",
        "intent": "Executive review",
        "summary": "General executive snapshot generated from current workspace signals.",
        "findings": [
            "Los ingresos previstos mantienen tendencia positiva.",
            "Persisten alertas en cuentas con baja actividad.",
            "El sistema recomienda revisar pricing y follow-ups pendientes.",
        ],
        "actions": ["Refresh cockpit", "Open risky accounts", "Inspect active agents"],
    }


def _render_ai_command_layer() -> None:
    st.markdown("### AI Command Layer")
    command = st.text_input(
        "Ask the operating system what to do next",
        value=st.session_state.get("intelligence_command", ""),
        placeholder="Show risky accounts",
        key="intelligence_command_input",
    )
    suggestion_cols = st.columns(len(_COMMAND_SUGGESTIONS))
    for idx, suggestion in enumerate(_COMMAND_SUGGESTIONS):
        with suggestion_cols[idx]:
            if st.button(suggestion, key=f"cmd_suggestion_{idx}", use_container_width=True):
                st.session_state["intelligence_command"] = suggestion
                st.session_state["intelligence_command_result"] = _classify_command(suggestion)
                st.rerun()

    if st.button("Run AI command", type="primary", key="run_intelligence_command", use_container_width=True):
        st.session_state["intelligence_command"] = command
        st.session_state["intelligence_command_result"] = _classify_command(command or "Executive review")

    result = st.session_state.get("intelligence_command_result")
    if not result:
        return

    st.success(f"{result['intent']} → {result['workspace']}")
    st.caption(result["summary"])
    col1, col2 = st.columns([2, 1])
    with col1:
        with st.expander("Executive Summary", expanded=True):
            for finding in result["findings"]:
                st.write(f"• {finding}")
    with col2:
        with st.expander("Recommended Actions", expanded=True):
            for action in result["actions"]:
                st.write(f"→ {action}")
        if st.button("Open recommended workspace", key="open_command_workspace", use_container_width=True):
            st.session_state["active_page"] = result["workspace"]
            st.rerun()


def _render_insight_feed() -> None:
    insights = [
        ("⚠️ Alta prioridad", "Cliente Atlas bajó actividad 27%", "Motivos: 34 días sin respuesta, 2 propuestas rechazadas.", "Abrir cuenta"),
        ("📈 Oportunidad", "Opportunity Nova mejoró su probabilidad", "Motivos: nueva reunión, stakeholders activos, mayor ticket.", "Revisar deal"),
        ("🚨 Riesgo", "Pricing fuera de rango en oferta Delta", "Motivos: descuento 18% superior al benchmark.", "Validar pricing"),
    ]
    cols = st.columns(3)
    for idx, (severity, title, reason, action) in enumerate(insights):
        with cols[idx]:
            st.markdown(f"**{title}**")
            st.caption(severity)
            st.write(reason)
            st.button(action, key=f"insight_action_{idx}", use_container_width=True)


def _render_alerts_and_sources() -> None:
    left, right = st.columns([3, 2])
    with left:
        st.markdown("### Alerts & Risks")
        alerts = pd.DataFrame(
            [
                {"Alert": "Cliente Boreal sin respuesta", "Severity": "High", "Why": "34 días sin actividad"},
                {"Alert": "Oferta Delta con pricing anómalo", "Severity": "High", "Why": "Descuento 18% sobre benchmark"},
                {"Alert": "Pipeline EMEA con conversión baja", "Severity": "Medium", "Why": "Caída del 11% semanal"},
            ]
        )
        st.dataframe(alerts, use_container_width=True, hide_index=True)
    with right:
        st.markdown("### Source Traceability")
        st.caption("Every insight keeps its evidence trail.")
        st.markdown("- Email: `renewal-thread-atlas.eml`")
        st.markdown("- PDF: `pricing-delta-q2.pdf`")
        st.markdown("- CRM note: `nova-opportunity-2026-05-08`")
        st.markdown("- Confidence score: `0.86 – 0.94`")


def render_default_dashboard() -> None:
    today = datetime.now().strftime("%Y-%m-%d")

    st.markdown("## 🧠 Intelligence Center")
    st.caption(f"Commercial Intelligence Operating System · {today}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Revenue forecast", "€5.2M", delta="+8.4%")
    col2.metric("Deals at risk", "7", delta="+2")
    col3.metric("Urgent alerts", "4", delta="-1")
    col4.metric("Top opportunities", "12", delta="+3")

    _render_ai_command_layer()

    st.markdown("### Workspace Snapshot")
    _render_workspace_cards()

    st.markdown("### AI Insights Feed")
    _render_insight_feed()

    col_left, col_right = st.columns([2, 1])
    with col_left:
        _render_alerts_and_sources()
    with col_right:
        st.markdown("### Action Recommendations")
        st.write("→ Contactar a Cliente Atlas con propuesta de reactivación.")
        st.write("→ Revisar pricing de Oferta Delta antes de enviar.")
        st.write("→ Generar brief ejecutivo de Opportunity Nova.")
        st.write("→ Lanzar workflow de seguimiento para cuentas sin respuesta.")

        st.markdown("### Agent Center")
        agents = pd.DataFrame(
            [
                {"Agent": "Research Agent", "Status": "Running", "Last action": "Synthesized 12 sources"},
                {"Agent": "Pricing Agent", "Status": "Attention", "Last action": "Flagged Delta anomaly"},
                {"Agent": "Forecast Agent", "Status": "Healthy", "Last action": "Updated revenue outlook"},
            ]
        )
        st.dataframe(agents, use_container_width=True, hide_index=True)
