"""Smart Plant Dashboard with multi-site Ingecart monitoring and live signal simulation."""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from backoffice.analytics.ingecart_monitoring import (
    FORMULA_LIBRARY,
    ROLE_PANELS,
    generate_instant_offer,
    generate_monitoring_snapshot,
    get_scope_label,
    load_monitoring_blueprint,
)


st.set_page_config(page_title="INGECART Smart Plant Dashboard", page_icon="🏭", layout="wide")
CONFIG_PATH = Path("data/smart_plant_config.json")


def load_config() -> dict:
    default = {
        "overview_text": "INGECART Smart Plant Dashboard",
        "general_video_path": "assets/videos/general/overview.mp4",
        "plant_image_path": "assets/images/smart_plant_overview.png",
        "hotspots": [],
        "kpis": {"productivity": 67, "automation": 82, "labor": 34, "waste": 12},
        "subpages": [],
        "solutions_mapping": {},
    }
    if CONFIG_PATH.exists():
        try:
            loaded = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            loaded = default
        for key, value in default.items():
            loaded.setdefault(key, value)
        return loaded
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")
    return default


def render_plant(config: dict, snapshot: dict | None = None) -> None:
    del config
    if snapshot:
        st.info(
            f'Scope activo: {snapshot["scope_label"]} · '
            f'{len(snapshot["equipment_latest"])} activos · '
            f'{snapshot["simulation_assumptions"]["shift_count"]} turnos / 1 festivo semanal'
        )
    else:
        st.info("Capa de monitorización cargada.")


def _inject_local_styles() -> None:
    st.markdown(
        """
        <style>
          .hero-card {background:linear-gradient(135deg,#161920 0%,#0d0f13 100%);border:1px solid #2A2D38;border-radius:16px;padding:22px 26px;margin-bottom:16px;}
          .hero-card h1 {margin:0;color:#FF6A00;font-size:34px;}
          .hero-card p, .hero-card li {color:#D5D8E0;}
          .scope-chip {display:inline-block;padding:6px 10px;border-radius:999px;background:rgba(255,106,0,0.14);color:#FF8330;font-weight:600;margin-right:8px;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_header(snapshot: dict) -> None:
    portfolio = snapshot["portfolio"]
    st.markdown(
        f"""
        <div class="hero-card">
          <div class="scope-chip">{snapshot["scope_label"]}</div>
          <div class="scope-chip">{snapshot["role"]}</div>
          <h1>INGECART Monitoring Copilot</h1>
          <p>
            Gemelo operativo multi-planta con señales simuladas en tiempo real para paletización,
            conveyors, BHS handoff, AMRs, Ingetrans y RFID. Stack elegido:
            <strong>{snapshot["blueprint"]["recommended_stack"]}</strong>.
          </p>
          <ul>
            <li>OEE portfolio: <strong>{portfolio["oee_pct"]}%</strong></li>
            <li>Alertas activas: <strong>{portfolio["active_alerts"]}</strong></li>
            <li>Potencial anual recuperable: <strong>EUR {portfolio["annual_recovery_potential_eur"]:.0f}</strong></li>
          </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_site_cards(site_summaries: list[dict]) -> None:
    cols = st.columns(max(1, min(3, len(site_summaries))))
    for index, site in enumerate(site_summaries):
        with cols[index % len(cols)]:
            st.markdown(f"#### {site['site_id']} · {site['site_name']}")
            st.metric("OEE", f"{site['oee_pct']}%")
            st.metric("Activos críticos", site["critical_assets"])
            st.metric("PM próximas", site["pm_due_assets"])
            st.caption(site["summary"])


def main() -> None:
    try:
        from backoffice.theme import inject_theme

        inject_theme()
    except Exception:
        pass

    import pandas as pd
    import plotly.express as px

    _inject_local_styles()
    config = load_config()
    blueprint = load_monitoring_blueprint()

    with st.sidebar:
        st.markdown("## 🏭 Ingecart Monitoring")
        role_names = list(ROLE_PANELS.keys())
        role = st.selectbox("Rol", role_names, index=role_names.index("Ingecart"))
        scope_values = ["all"] + [site["id"] for site in blueprint["sites"]]
        scope = st.selectbox("Vista", scope_values, format_func=lambda value: get_scope_label(value, blueprint))
        days = st.slider("Horizonte histórico (días)", min_value=3, max_value=14, value=7)
        interval_minutes = st.select_slider("Resolución", options=[15, 30, 60], value=15)
        st.caption(ROLE_PANELS[role]["description"])

    snapshot = generate_monitoring_snapshot(
        site_scope=scope,
        role=role,
        days=days,
        interval_minutes=interval_minutes,
        blueprint=blueprint,
    )

    _render_header(snapshot)
    render_plant(config, snapshot=snapshot)

    series_df = pd.DataFrame(snapshot["series"])
    series_df["timestamp"] = pd.to_datetime(series_df["timestamp"])
    latest_df = pd.DataFrame(snapshot["equipment_latest"])
    sites_df = pd.DataFrame(snapshot["site_summaries"])
    alerts_df = pd.DataFrame(snapshot["alerts"])
    interventions_df = pd.DataFrame(snapshot["interventions"])
    recommendations_df = pd.DataFrame(snapshot["recommendations"])
    formulas_df = pd.DataFrame(FORMULA_LIBRARY)

    metric_cols = st.columns(5)
    metric_cols[0].metric("OEE portfolio", f'{snapshot["portfolio"]["oee_pct"]}%')
    metric_cols[1].metric("Disponibilidad", f'{snapshot["portfolio"]["availability_pct"]}%')
    metric_cols[2].metric("Alertas", snapshot["portfolio"]["active_alerts"])
    metric_cols[3].metric("Energía/semana", f'{snapshot["portfolio"]["energy_mwh_week"]} MWh')
    metric_cols[4].metric("Negocio servicio", f'EUR {snapshot["portfolio"]["service_opportunity_eur"]:.0f}')

    tab_overview, tab_signals, tab_maintenance, tab_ai, tab_reports = st.tabs(
        ["Executive Twin", "Live Signals", "Maintenance & Service", "AI Copilot", "Reports & Offers"]
    )

    with tab_overview:
        _render_site_cards(snapshot["site_summaries"])
        if not sites_df.empty:
            st.plotly_chart(
                px.bar(
                    sites_df,
                    x="site_name",
                    y=["oee_pct", "availability_pct", "performance_pct", "quality_pct"],
                    barmode="group",
                    title="KPIs por planta",
                ),
                use_container_width=True,
            )
            st.dataframe(
                sites_df[
                    [
                        "site_id",
                        "site_name",
                        "oee_pct",
                        "lpi_pct",
                        "critical_assets",
                        "pm_due_assets",
                        "annual_recovery_potential_eur",
                    ]
                ],
                use_container_width=True,
            )

    with tab_signals:
        equipment_values = ["all"] + latest_df["equipment_id"].tolist()
        selected_equipment = st.selectbox(
            "Equipo",
            equipment_values,
            format_func=lambda value: "Todos los equipos" if value == "all" else latest_df.loc[latest_df["equipment_id"] == value, "equipment_name"].iloc[0],
        )
        signal_options = [
            "oee_pct",
            "throughput_per_hour",
            "predicted_failure_risk_pct",
            "queue_pct",
            "temperature_c",
            "vibration_mm_s",
            "battery_pct",
            "reel_moves_h",
            "rfid_reads_h",
            "lpi_pct",
        ]
        signal = st.selectbox("Señal", signal_options)
        chart_df = series_df.copy()
        if selected_equipment != "all":
            chart_df = chart_df[chart_df["equipment_id"] == selected_equipment]
        chart_df = chart_df[chart_df[signal].notna()]
        if not chart_df.empty:
            st.plotly_chart(
                px.line(
                    chart_df,
                    x="timestamp",
                    y=signal,
                    color="equipment_name" if selected_equipment == "all" else None,
                    title=f"Señal simulada · {signal}",
                ),
                use_container_width=True,
            )
        st.dataframe(
            latest_df[
                [
                    "site_name",
                    "equipment_name",
                    "state",
                    "oee_pct",
                    "throughput_per_hour",
                    "queue_pct",
                    "predicted_failure_risk_pct",
                    "alarm_count",
                ]
            ],
            use_container_width=True,
        )

    with tab_maintenance:
        if not latest_df.empty:
            st.plotly_chart(
                px.scatter(
                    latest_df,
                    x="maintenance_due_days",
                    y="predicted_failure_risk_pct",
                    color="site_name",
                    size="cost_of_downtime_eur_h",
                    hover_name="equipment_name",
                    title="Riesgo vs preventivo pendiente",
                ),
                use_container_width=True,
            )
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("Solicitudes de intervención")
            if not interventions_df.empty:
                st.dataframe(interventions_df, use_container_width=True)
            else:
                st.success("Sin intervenciones prioritarias en este alcance.")
        with col_b:
            st.subheader("Contratos recomendados")
            contracts_df = pd.DataFrame(snapshot["contracts"])
            if not contracts_df.empty:
                st.dataframe(contracts_df, use_container_width=True)
            else:
                st.info("No se han generado oportunidades contractuales para este alcance.")

    with tab_ai:
        st.subheader("Copilot de recomendaciones")
        if not recommendations_df.empty:
            st.dataframe(recommendations_df, use_container_width=True)
        else:
            st.info("Sin recomendaciones para este alcance.")
        if role == "Ingecart":
            hidden_df = pd.DataFrame(snapshot["hidden_issues"])
            st.subheader("Problemas latentes detectados por Ingecart")
            if not hidden_df.empty:
                st.dataframe(hidden_df, use_container_width=True)
            else:
                st.success("No se detectan problemas latentes sin reportar.")
        with st.expander("Biblioteca de fórmulas de panel"):
            st.dataframe(formulas_df, use_container_width=True)

    with tab_reports:
        st.subheader("Informe automático")
        st.text_area("Preview", snapshot["report_markdown"], height=320)
        st.download_button(
            "Descargar informe .md",
            data=snapshot["report_markdown"].encode("utf-8"),
            file_name=f'ingecart_monitoring_{scope}_{role.lower()}.md',
            mime="text/markdown",
        )
        st.download_button(
            "Descargar señales .csv",
            data=series_df.to_csv(index=False).encode("utf-8"),
            file_name=f'ingecart_signals_{scope}.csv',
            mime="text/csv",
        )
        st.markdown("---")
        st.subheader("Solicitud inmediata a Ingecart")
        offer_col_1, offer_col_2, offer_col_3 = st.columns(3)
        with offer_col_1:
            request_kind = st.selectbox(
                "Tipo de solicitud",
                ["maintenance_contract", "materials_and_spares", "intervention", "improvement_upgrade"],
                format_func=lambda value: {
                    "maintenance_contract": "Contrato de mantenimiento",
                    "materials_and_spares": "Materiales y repuestos",
                    "intervention": "Intervención",
                    "improvement_upgrade": "Mejora / upgrade",
                }[value],
            )
        with offer_col_2:
            target_equipment = st.selectbox(
                "Equipo objetivo",
                ["all"] + latest_df["equipment_id"].tolist(),
                format_func=lambda value: "Todos los equipos del alcance" if value == "all" else latest_df.loc[latest_df["equipment_id"] == value, "equipment_name"].iloc[0],
            )
        with offer_col_3:
            coverage = st.selectbox("Cobertura", ["business_hours", "extended", "24x7"], index=2)
        urgency = st.radio("Urgencia", ["standard", "priority", "emergency"], horizontal=True, index=1)
        offer = generate_instant_offer(snapshot, request_kind, target_equipment, coverage, urgency)
        offer_df = pd.DataFrame(offer["lines"])
        offer_metric_cols = st.columns(4)
        offer_metric_cols[0].metric("Referencia", offer["reference"])
        offer_metric_cols[1].metric("CAPEX", f'EUR {offer["capex_total_eur"]:.0f}')
        offer_metric_cols[2].metric("OPEX mensual", f'EUR {offer["monthly_total_eur"]:.0f}')
        offer_metric_cols[3].metric("SLA", f'{offer["response_sla_hours"]} h')
        st.dataframe(offer_df, use_container_width=True)
        st.write(offer["notes"])
        st.download_button(
            "Descargar oferta .json",
            data=json.dumps(offer, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name=f'{offer["reference"]}.json',
            mime="application/json",
        )

    if not alerts_df.empty:
        with st.expander("Alertas activas"):
            st.dataframe(alerts_df, use_container_width=True)


if __name__ == "__main__":
    main()
