"""Smart Plant Dashboard with multi-site Ingecart monitoring and live signal simulation."""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

try:
    from backoffice.analytics.ingecart_monitoring import (
        FORMULA_LIBRARY,
        ROLE_PANELS,
        build_request_alert,
        generate_instant_offer,
        generate_monitoring_snapshot,
        get_scope_label,
        load_monitoring_blueprint,
        suggest_spare_parts,
    )
except Exception:  # pragma: no cover - graceful fallback for optional monitoring module
    def load_monitoring_blueprint():
        return {
            "name": "INGECART Smart Plant Monitoring",
            "recommended_stack": "Streamlit + Plotly + FastAPI",
            "sites": [
                {"id": "site_001", "name": "Planta Norte", "country": "ES", "critical_assets": 12, "equipment": [{"id": "site_001_asset_01", "name": "Corrugadora 01", "status": "running"}]},
                {"id": "site_002", "name": "Planta Centro", "country": "FR", "critical_assets": 10, "equipment": [{"id": "site_002_asset_01", "name": "Ingetrans 01", "status": "warning"}]},
                {"id": "site_003", "name": "Planta Sur", "country": "IT", "critical_assets": 11, "equipment": [{"id": "site_003_asset_01", "name": "AMR 01", "status": "running"}]},
                {"id": "site_004", "name": "Planta Este", "country": "DE", "critical_assets": 9, "equipment": [{"id": "site_004_asset_01", "name": "Paletizador 01", "status": "running"}]},
                {"id": "site_005", "name": "Planta Oeste", "country": "PT", "critical_assets": 8, "equipment": [{"id": "site_005_asset_01", "name": "SR-1400", "status": "running"}]},
            ],
            "plants": [
                {"id": "site_001", "name": "Planta Norte"},
                {"id": "site_002", "name": "Planta Centro"},
                {"id": "site_003", "name": "Planta Sur"},
                {"id": "site_004", "name": "Planta Este"},
                {"id": "site_005", "name": "Planta Oeste"},
            ],
        }

    def get_scope_label(scope, blueprint=None):
        return "Portfolio global" if scope in (None, "", "all") else str(scope)

    def generate_monitoring_snapshot(site_scope="all", role="Ingecart", days=7, interval_minutes=15, blueprint=None):
        bp = blueprint or load_monitoring_blueprint()
        selected = bp["sites"] if site_scope in (None, "", "all") else [site for site in bp["sites"] if site["id"] == site_scope]
        site_summaries = [
            {"site_id": site["id"], "site_name": site["name"], "oee_pct": 86 + idx, "lpi_pct": 86 + idx, "critical_assets": site.get("critical_assets", 8), "pm_due_assets": 1, "annual_recovery_potential_eur": 150000 + idx * 20000, "summary": "Planta restaurada"}
            for idx, site in enumerate(selected)
        ]
        equipment_latest = [
            {"equipment_id": asset["id"], "site_id": site["id"], "site_name": site["name"], "equipment_name": asset["name"], "status": asset.get("status", "running"), "oee_pct": 85, "availability_pct": 90, "performance_pct": 88, "quality_pct": 98, "alert_count": 0 if asset.get("status") == "running" else 1, "last_seen_minutes_ago": 5}
            for site in selected
            for asset in site.get("equipment", [])
        ]
        return {
            "scope": site_scope,
            "scope_label": get_scope_label(site_scope),
            "role": role,
            "portfolio": {"oee_pct": 85, "availability_pct": 91, "active_alerts": sum(1 for e in equipment_latest if e["status"] == "warning"), "energy_mwh_week": 0, "annual_recovery_potential_eur": sum(s["annual_recovery_potential_eur"] for s in site_summaries), "service_opportunity_eur": 0},
            "site_summaries": site_summaries,
            "equipment_latest": equipment_latest,
            "series": [],
            "alerts": [],
            "interventions": [],
            "recommendations": [],
            "blueprint": bp,
            "simulation_assumptions": {"shift_count": 1, "interval_minutes": interval_minutes, "days": days},
        }

    def build_request_alert(*args, **kwargs):
        return {"customer_name": kwargs.get("customer_name", "Cliente"), "request_type": kwargs.get("request_type", "solicitud"), "urgency": kwargs.get("urgency", "media"), "details": kwargs.get("details", "")}

    def generate_instant_offer(*args, **kwargs):
        return {"title": "Oferta demo", "scope": kwargs.get("site_scope", "all"), "role": kwargs.get("role", "Ingecart"), "estimated_roi_pct": 0, "annual_savings_eur": 0.0, "payback_months": 0, "recommended_actions": [], "confidence": 0.0}

    def suggest_spare_parts(*args, **kwargs):
        return []

    FORMULA_LIBRARY = []
    ROLE_PANELS = {"Ingecart": {"description": "Modo de seguridad: la pantalla analítica no está disponible."}}


st.set_page_config(page_title="INGECART Smart Plant Dashboard", page_icon="🏭", layout="wide")
CONFIG_PATH = Path("data/smart_plant_config.json")


def load_config() -> dict:
    default = {
        "overview_text": "INGECART Smart Plant Dashboard",
        "general_video_path": "assets/videos/general/overview.mp4",
        "plant_image_path": "assets/images/smart_plant_overview.png",
        "hotspots": [],
        "plants": [
            {"id": "site_001", "name": "Planta Norte", "country": "ES", "region": "Europa", "status": "online", "equipment": [{"id": "site_001_asset_01", "name": "Corrugadora 01", "type": "corrugator", "status": "running"}, {"id": "site_001_asset_02", "name": "Ingetrans 01", "type": "intralogistics", "status": "warning"}]},
            {"id": "site_002", "name": "Planta Centro", "country": "FR", "region": "Europa", "status": "online", "equipment": [{"id": "site_002_asset_01", "name": "Corrugadora 02", "type": "corrugator", "status": "running"}, {"id": "site_002_asset_02", "name": "SR-1400", "type": "waste_system", "status": "warning"}]},
            {"id": "site_003", "name": "Planta Sur", "country": "IT", "region": "Europa", "status": "online", "equipment": [{"id": "site_003_asset_01", "name": "Corrugadora 03", "type": "corrugator", "status": "running"}, {"id": "site_003_asset_02", "name": "AMR 01", "type": "amr", "status": "running"}]},
            {"id": "site_004", "name": "Planta Este", "country": "DE", "region": "Europa", "status": "online", "equipment": [{"id": "site_004_asset_01", "name": "AMR 02", "type": "amr", "status": "running"}, {"id": "site_004_asset_02", "name": "Ingetrans 02", "type": "intralogistics", "status": "warning"}]},
            {"id": "site_005", "name": "Planta Oeste", "country": "PT", "region": "Europa", "status": "online", "equipment": [{"id": "site_005_asset_01", "name": "Corrugadora 05", "type": "corrugator", "status": "running"}, {"id": "site_005_asset_02", "name": "Palletizador 01", "type": "palletizer", "status": "warning"}]},
        ],
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


def _ensure_request_alert_state() -> None:
    st.session_state.setdefault("ingecart_request_alerts", [])
    st.session_state.setdefault("ingecart_spare_matches", [])


def main() -> None:
    try:
        from backoffice.theme import inject_theme

        inject_theme()
    except Exception:
        pass

    import pandas as pd
    import plotly.express as px

    _inject_local_styles()
    _ensure_request_alert_state()
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
        if role == "Ingecart":
            st.markdown("#### Alerta-Nueva solicitud (clientes)")
            customer_alerts = st.session_state.get("ingecart_request_alerts", [])
            if customer_alerts:
                st.dataframe(pd.DataFrame(customer_alerts), use_container_width=True)
            else:
                st.caption("No hay solicitudes nuevas de clientes registradas en esta sesión.")

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
        requester_col_1, requester_col_2, requester_col_3 = st.columns(3)
        with requester_col_1:
            requester_name = st.text_input("Solicitante", placeholder="Nombre del solicitante")
        with requester_col_2:
            requester_role = st.selectbox("Perfil del solicitante", ["Operario", "Mantenimiento", "Jefe de planta", "Compras", "Gerencia"], index=3)
        with requester_col_3:
            request_site_id = st.selectbox(
                "Planta solicitante",
                [site["id"] for site in blueprint["sites"]],
                format_func=lambda value: next((f'{site["id"]} · {site["name"]}' for site in blueprint["sites"] if site["id"] == value), value),
            )

        spare_description = ""
        if request_kind == "materials_and_spares":
            st.markdown("#### Buscador técnico de recambios")
            spare_description = st.text_area(
                "Descripción técnica disponible del recambio",
                placeholder="Ejemplo: variador 7.5 kW 400V con STO para cinta transportadora",
                height=100,
            )
            if st.button("Buscar recambios compatibles", use_container_width=True):
                st.session_state["ingecart_spare_matches"] = suggest_spare_parts(spare_description, top_k=8)

            spare_matches = st.session_state.get("ingecart_spare_matches", [])
            if spare_matches:
                rows = []
                for match in spare_matches:
                    alternatives = "; ".join(
                        f'{alt["vendor"]} {alt["code"]}: {alt["technical_description"]}'
                        for alt in match["compatible_alternatives"]
                    )
                    rows.append(
                        {
                            "Familia": match["family_group"],
                            "Código original (OEM)": match["oem_code"],
                            "Descripción técnica": match["technical_description"],
                            "Alternativas compatibles mercado": alternatives,
                        }
                    )
                st.dataframe(pd.DataFrame(rows), use_container_width=True)
            else:
                st.caption("Introduce una descripción técnica para proponer códigos originales y alternativas compatibles.")

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
        if st.button("Registrar solicitud y generar Alerta-Nueva solicitud", use_container_width=True):
            site_name = next((site["name"] for site in blueprint["sites"] if site["id"] == request_site_id), "Planta no identificada")
            description = spare_description if request_kind == "materials_and_spares" else f"Solicitud de tipo {request_kind} para {target_equipment}."
            suggestions = st.session_state.get("ingecart_spare_matches", []) if request_kind == "materials_and_spares" else []
            if request_kind == "materials_and_spares" and not spare_description.strip():
                st.warning("Para recambios, añade una descripción técnica antes de registrar la solicitud.")
            else:
                alert = build_request_alert(
                    request_kind=request_kind,
                    requester_name=requester_name,
                    requester_role=requester_role,
                    plant_id=request_site_id,
                    plant_name=site_name,
                    urgency=urgency,
                    description=description,
                    suggested_parts=suggestions,
                )
                st.session_state["ingecart_request_alerts"] = [alert] + st.session_state.get("ingecart_request_alerts", [])
                st.success("Solicitud registrada. Visible para Ingecart en 'Alerta-Nueva solicitud'.")

    if not alerts_df.empty:
        with st.expander("Alertas activas"):
            st.dataframe(alerts_df, use_container_width=True)
    customer_alerts = st.session_state.get("ingecart_request_alerts", [])
    if customer_alerts:
        with st.expander("Alerta-Nueva solicitud (clientes)"):
            st.dataframe(pd.DataFrame(customer_alerts), use_container_width=True)


if __name__ == "__main__":
    main()
