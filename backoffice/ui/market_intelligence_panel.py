"""Streamlit panel for Web Intelligence & Market Research."""
from __future__ import annotations

import json
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

from backoffice.intelligence.crawler import IntelligenceCrawler
from backoffice.intelligence.pipeline import TASK_TYPES, pipeline
from backoffice.intelligence.storage import intelligence_db

# ── Playwright availability ───────────────────────────────────────────────────
try:
    from playwright.sync_api import sync_playwright  # noqa: F401
    _PLAYWRIGHT_OK = True
except ImportError:
    _PLAYWRIGHT_OK = False

# ── Module-level task registry (thread-safe across Streamlit reruns) ──────────
_intel_tasks: Dict[str, Dict[str, Any]] = {}


def _task_worker(task_id: str, kwargs: Dict[str, Any]) -> None:
    progress: List[str] = _intel_tasks[task_id]["progress"]

    def cb(msg: str) -> None:
        progress.append(msg)

    try:
        result = pipeline.run(**kwargs, progress_callback=cb)
        _intel_tasks[task_id].update({"status": "completed", "result": result})
    except Exception as exc:
        _intel_tasks[task_id].update({"status": "failed", "error": str(exc)})


def _start_task(kwargs: Dict[str, Any]) -> str:
    task_id = datetime.now().strftime("%Y%m%d_%H%M%S_") + kwargs["task_type"]
    _intel_tasks[task_id] = {"status": "running", "progress": [], "kwargs": kwargs}
    t = threading.Thread(target=_task_worker, args=(task_id, kwargs), daemon=True)
    t.start()
    return task_id


# ── Session state init ────────────────────────────────────────────────────────

def _init_state() -> None:
    if "intel_active_task" not in st.session_state:
        st.session_state.intel_active_task = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _df(rows: List[Dict], cols: Optional[List[str]] = None) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if cols:
        present = [c for c in cols if c in df.columns]
        df = df[present]
    return df


def _badge(text: str, color: str = "#3b82f6") -> str:
    return (
        f'<span style="background:{color};color:#fff;padding:2px 8px;'
        f'border-radius:10px;font-size:11px;font-weight:600">{text}</span>'
    )


_TYPE_COLORS = {
    "market_intel": "#0ea5e9",
    "leads":        "#10b981",
    "content":      "#f59e0b",
    "research":     "#8b5cf6",
    "monitoring":   "#ef4444",
    "operational":  "#64748b",
}


# ── Main panel ────────────────────────────────────────────────────────────────

class MarketIntelligencePanel:
    """Comprehensive Web Intelligence panel with 6 specialised tabs."""

    def render(self) -> None:
        _init_state()

        st.title("🕵️ Web Intelligence & Market Research")
        st.markdown(
            "*Deep crawling multi-nivel · Inteligencia competitiva · Leads B2B · "
            "Agregación de contenido · Monitorización automática*"
        )
        if not _PLAYWRIGHT_OK:
            st.info(
                "💡 **Renderizado JS no disponible.** Para activarlo: "
                "`pip install playwright && playwright install chromium`",
                icon="ℹ️",
            )

        # ── KPI bar ───────────────────────────────────────────────
        stats = intelligence_db.get_stats()
        cols = st.columns(6)
        kpis = [
            ("Sesiones",   stats.get("crawl_sessions", 0),     "🔄"),
            ("Páginas",    stats.get("scraped_pages", 0),       "📄"),
            ("Market",     stats.get("market_intelligence", 0), "📊"),
            ("Leads",      stats.get("leads", 0),               "👥"),
            ("Contenido",  stats.get("content_items", 0),       "📰"),
            ("Alertas",    stats.get("monitoring_alerts", 0),   "🔔"),
        ]
        for col, (label, val, icon) in zip(cols, kpis):
            col.metric(f"{icon} {label}", val)

        st.divider()

        tabs = st.tabs([
            "🔍 Nueva Búsqueda",
            "📊 Intel de Mercado",
            "👥 Leads B2B",
            "📰 Contenido",
            "👁️ Monitorización",
            "📈 Informes",
        ])

        with tabs[0]: self._tab_search()
        with tabs[1]: self._tab_market()
        with tabs[2]: self._tab_leads()
        with tabs[3]: self._tab_content()
        with tabs[4]: self._tab_monitoring()
        with tabs[5]: self._tab_reports()

    # ── Tab 0: Nueva Búsqueda ─────────────────────────────────────

    def _tab_search(self) -> None:
        st.subheader("🔍 Nueva búsqueda de inteligencia")

        with st.form("intel_search_form"):
            # ── Task type ──────────────────────────────────────────
            task_type = st.selectbox(
                "Tipo de tarea",
                list(TASK_TYPES.keys()),
                format_func=lambda k: f"{k} — {TASK_TYPES[k]}",
            )

            query = st.text_input(
                "🎯 Tema / Query",
                placeholder="Ej: maquinaria corrugadora OEM Europa, software gestión logística…",
            )

            urls_raw = st.text_area(
                "🌐 URLs de inicio (una por línea)",
                placeholder="https://www.ejemplo.com\nhttps://www.otro.com/productos",
                height=120,
            )

            keywords_raw = st.text_input(
                "🔑 Keywords de filtrado (separadas por coma)",
                placeholder="corrugado, packaging, automation",
                help="Solo se guardan páginas que contengan alguno de estos términos",
            )

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                max_pages = st.number_input("Máx. páginas", 5, 200, 30)
            with col2:
                max_depth = st.number_input("Profundidad", 1, 5, 2)
            with col3:
                use_js = st.toggle(
                    "Renderizar JS",
                    value=False,
                    disabled=not _PLAYWRIGHT_OK,
                    help="Requiere Playwright instalado",
                )
            with col4:
                same_domain = st.toggle("Solo mismo dominio", value=True)

            exclude_raw = st.text_input(
                "⛔ Excluir URLs que contengan (separadas por coma)",
                placeholder="/login, /cart, /checkout",
            )

            submitted = st.form_submit_button("🚀 Iniciar crawl", type="primary")

        if submitted:
            start_urls = [u.strip() for u in urls_raw.splitlines() if u.strip()]
            if not start_urls:
                st.error("Introduce al menos una URL de inicio.")
            elif not query:
                st.error("Introduce un query / tema.")
            else:
                keywords = (
                    [k.strip() for k in keywords_raw.split(",") if k.strip()]
                    if keywords_raw else None
                )
                exclude_patterns = (
                    [e.strip() for e in exclude_raw.split(",") if e.strip()]
                    if exclude_raw else None
                )
                task_id = _start_task({
                    "task_type":        task_type,
                    "query":            query,
                    "start_urls":       start_urls,
                    "max_pages":        int(max_pages),
                    "max_depth":        int(max_depth),
                    "use_js":           use_js,
                    "keywords":         keywords,
                    "exclude_patterns": exclude_patterns,
                })
                st.session_state.intel_active_task = task_id
                st.success(f"✅ Tarea iniciada: `{task_id}`")
                st.rerun()

        # ── Active task monitor ────────────────────────────────────
        active_id = st.session_state.get("intel_active_task")
        if active_id and active_id in _intel_tasks:
            task = _intel_tasks[active_id]
            status = task["status"]
            color = {"running": "#f59e0b", "completed": "#10b981", "failed": "#ef4444"}.get(status, "#64748b")
            st.markdown(
                f"### Tarea activa &nbsp; {_badge(status.upper(), color)}",
                unsafe_allow_html=True,
            )
            st.caption(f"ID: `{active_id}`")

            progress = task.get("progress", [])
            if progress:
                with st.expander(f"📋 Log ({len(progress)} mensajes)", expanded=status == "running"):
                    st.text("\n".join(progress[-60:]))

            if status == "running":
                col_r, col_s = st.columns([1, 4])
                with col_r:
                    if st.button("🔄 Actualizar"):
                        st.rerun()
            elif status == "completed":
                result = task.get("result", {})
                counts = result.get("counts", {})
                st.success(
                    f"Completado · Páginas: **{counts.get('pages', 0)}** · "
                    f"Market: **{counts.get('market', 0)}** · "
                    f"Leads: **{counts.get('leads', 0)}** · "
                    f"Contenido: **{counts.get('content', 0)}**"
                )
                if st.button("➕ Nueva búsqueda"):
                    st.session_state.intel_active_task = None
                    st.rerun()
            elif status == "failed":
                st.error(f"❌ Error: {task.get('error', 'Desconocido')}")

        # ── Recent sessions ───────────────────────────────────────
        st.divider()
        st.subheader("📜 Sesiones recientes")
        sessions = intelligence_db.get_sessions(limit=10)
        if sessions:
            df = _df(sessions, ["task_type", "query", "status", "created_at", "completed_at"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay sesiones todavía. Inicia una búsqueda.")

    # ── Tab 1: Market Intelligence ────────────────────────────────

    def _tab_market(self) -> None:
        st.subheader("📊 Inteligencia de Mercado y Competencia")

        col1, col2, col3 = st.columns(3)
        with col1:
            company_filter = st.text_input("Filtrar por empresa", key="mkt_company")
        with col2:
            cat_opts = ["", "machinery", "software", "services", "printing", "automation", "retail", "general"]
            cat_filter = st.selectbox("Categoría", cat_opts, key="mkt_cat")
        with col3:
            limit_mkt = st.number_input("Máx. registros", 10, 1000, 200, key="mkt_limit")

        items = intelligence_db.get_market_intel(
            company=company_filter or None,
            category=cat_filter or None,
            limit=int(limit_mkt),
        )

        if not items:
            st.info("Sin datos de mercado. Ejecuta una tarea de tipo **market_intel**.")
            return

        st.markdown(f"**{len(items)} registros encontrados**")

        # ── Competitor overview ────────────────────────────────────
        companies = list({i["company"] for i in items if i.get("company")})
        if companies:
            import plotly.express as px
            comp_counts = pd.Series([i["company"] for i in items]).value_counts().head(15)
            fig = px.bar(
                x=comp_counts.values, y=comp_counts.index,
                orientation="h",
                title="Top empresas detectadas",
                labels={"x": "Páginas", "y": "Empresa"},
            )
            fig.update_layout(height=350, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)

        # ── Products & prices table ────────────────────────────────
        st.markdown("### 🛒 Productos y precios detectados")
        rows = []
        for item in items:
            for prod in item.get("products", []):
                rows.append({
                    "Empresa":      item.get("company", ""),
                    "Producto":     prod.get("name", "")[:80],
                    "Precio":       prod.get("price", ""),
                    "Categoría":    item.get("category", ""),
                    "URL":          item.get("url", ""),
                    "Fecha":        (item.get("detected_at") or "")[:10],
                })

        if rows:
            df_prod = pd.DataFrame(rows)
            st.dataframe(df_prod, use_container_width=True, height=350)

            # Price mentions summary
            all_prices = []
            for item in items:
                all_prices.extend(item.get("prices", []))
            if all_prices:
                st.markdown(f"**💰 {len(all_prices)} menciones de precio encontradas:**")
                st.write(", ".join(all_prices[:30]))
        else:
            st.warning("No se encontraron productos estructurados. Prueba con páginas de catálogo o e-commerce.")

        # ── Raw table ─────────────────────────────────────────────
        with st.expander("📋 Tabla completa"):
            display_cols = ["company", "title", "category", "url", "detected_at"]
            df_full = _df(items, display_cols)
            st.dataframe(df_full, use_container_width=True)

        # ── Export ────────────────────────────────────────────────
        st.download_button(
            "📥 Exportar JSON",
            data=intelligence_db.export_json("market_intelligence"),
            file_name=f"market_intel_{datetime.now():%Y%m%d}.json",
            mime="application/json",
        )

    # ── Tab 2: Leads B2B ─────────────────────────────────────────

    def _tab_leads(self) -> None:
        st.subheader("👥 Generación de Leads B2B")

        col1, col2, col3 = st.columns(3)
        with col1:
            sector_filter = st.text_input("Sector", key="leads_sector")
        with col2:
            country_filter = st.text_input("País", key="leads_country")
        with col3:
            limit_leads = st.number_input("Máx. registros", 10, 2000, 500, key="leads_limit")

        leads = intelligence_db.get_leads(
            sector=sector_filter or None,
            country=country_filter or None,
            limit=int(limit_leads),
        )

        if not leads:
            st.info("Sin leads todavía. Ejecuta una tarea de tipo **leads**.")
            return

        st.markdown(f"**{len(leads)} leads encontrados**")

        # ── Charts ────────────────────────────────────────────────
        import plotly.express as px
        col_a, col_b = st.columns(2)
        with col_a:
            sectors = pd.Series([l["sector"] for l in leads if l.get("sector")]).value_counts()
            if not sectors.empty:
                fig = px.pie(values=sectors.values, names=sectors.index, title="Leads por sector")
                fig.update_layout(height=280, margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(fig, use_container_width=True)
        with col_b:
            countries = pd.Series([l["country"] for l in leads if l.get("country")]).value_counts()
            if not countries.empty:
                fig2 = px.bar(x=countries.values, y=countries.index, orientation="h",
                              title="Leads por país")
                fig2.update_layout(height=280, margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(fig2, use_container_width=True)

        # ── Table ─────────────────────────────────────────────────
        display = ["company", "contact_name", "role", "email", "phone",
                   "linkedin", "sector", "country", "source_url"]
        df = _df(leads, display)
        st.dataframe(df, use_container_width=True, height=400)

        # ── Export ────────────────────────────────────────────────
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            st.download_button(
                "📥 Exportar JSON",
                data=intelligence_db.export_json("leads"),
                file_name=f"leads_{datetime.now():%Y%m%d}.json",
                mime="application/json",
            )
        with col_e2:
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Exportar CSV",
                data=csv,
                file_name=f"leads_{datetime.now():%Y%m%d}.csv",
                mime="text/csv",
            )

    # ── Tab 3: Contenido ─────────────────────────────────────────

    def _tab_content(self) -> None:
        st.subheader("📰 Agregación de Contenido")

        col1, col2 = st.columns(2)
        with col1:
            type_filter = st.selectbox(
                "Tipo",
                ["", "news", "blog", "trend", "review", "report", "general"],
                key="content_type",
            )
        with col2:
            limit_content = st.number_input("Máx. registros", 10, 500, 100, key="content_limit")

        items = intelligence_db.get_content(
            content_type=type_filter or None,
            limit=int(limit_content),
        )

        if not items:
            st.info("Sin contenido todavía. Ejecuta una tarea de tipo **content** o **research**.")
            return

        st.markdown(f"**{len(items)} ítems de contenido**")

        # ── Type distribution ─────────────────────────────────────
        import plotly.express as px
        type_counts = pd.Series([i["type"] for i in items]).value_counts()
        if not type_counts.empty:
            fig = px.bar(
                x=type_counts.index, y=type_counts.values,
                title="Distribución por tipo",
                labels={"x": "Tipo", "y": "Cantidad"},
                color=type_counts.index,
            )
            fig.update_layout(height=250, margin=dict(l=0, r=0, t=40, b=0), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        # ── Content cards ─────────────────────────────────────────
        st.markdown("### 📑 Artículos y publicaciones")
        for item in items[:30]:
            with st.expander(
                f"{item.get('type', '').upper()} · {item.get('title', item.get('source_url', ''))[:100]}"
            ):
                if item.get("author"):
                    st.caption(f"✍️ {item['author']}  |  📅 {item.get('published_at', '')}")
                st.markdown(item.get("summary", ""))
                tags = item.get("tags", [])
                if tags:
                    st.markdown(" ".join(f"`{t}`" for t in tags))
                st.markdown(f"[🔗 Fuente]({item.get('source_url', '#')})")

        # ── Export ────────────────────────────────────────────────
        st.download_button(
            "📥 Exportar JSON",
            data=intelligence_db.export_json("content_items"),
            file_name=f"content_{datetime.now():%Y%m%d}.json",
            mime="application/json",
        )

    # ── Tab 4: Monitorización ─────────────────────────────────────

    def _tab_monitoring(self) -> None:
        st.subheader("👁️ Monitorización Automática de Competidores")

        col_add, col_list = st.columns([1, 2])

        with col_add:
            st.markdown("#### ➕ Añadir objetivo")
            with st.form("add_monitor_form"):
                mon_name  = st.text_input("Nombre", placeholder="Competidor A — precios")
                mon_url   = st.text_input("URL", placeholder="https://www.competidor.com/precios")
                mon_type  = st.selectbox("Tipo de monitorización", ["price", "product", "content"])
                mon_kws   = st.text_input("Keywords de alerta", placeholder="precio, oferta, descuento")
                submitted = st.form_submit_button("Registrar objetivo")

            if submitted:
                if not mon_url or not mon_name:
                    st.error("Nombre y URL son obligatorios.")
                else:
                    config = {
                        "keywords": [k.strip() for k in mon_kws.split(",") if k.strip()]
                    }
                    tid = intelligence_db.save_monitoring_target(
                        name=mon_name, url=mon_url,
                        monitor_type=mon_type, config=config,
                    )
                    st.success(f"✅ Objetivo registrado: `{tid[:8]}…`")
                    st.rerun()

        with col_list:
            st.markdown("#### 📋 Objetivos activos")
            targets = intelligence_db.get_monitoring_targets()
            if targets:
                for t in targets:
                    with st.expander(f"**{t['name']}** · {t['monitor_type']} · {t['url'][:60]}"):
                        st.json({k: v for k, v in t.items() if k != "config"})
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("🔍 Verificar ahora", key=f"mon_run_{t['id']}"):
                                with st.spinner("Verificando…"):
                                    alerts = pipeline.run_monitoring_check(t)
                                if alerts:
                                    st.warning(f"🔔 {len(alerts)} alerta(s) detectada(s)")
                                else:
                                    st.success("Sin cambios detectados")
                        with c2:
                            if st.button("⛔ Desactivar", key=f"mon_del_{t['id']}"):
                                intelligence_db.deactivate_monitoring_target(t["id"])
                                st.rerun()
            else:
                st.info("No hay objetivos de monitorización registrados.")

        # ── Alerts log ────────────────────────────────────────────
        st.divider()
        st.subheader("🔔 Alertas recientes")
        alerts = intelligence_db.get_alerts(limit=50)
        if alerts:
            df_alerts = _df(alerts, [
                "target_name", "alert_type", "description",
                "old_value", "new_value", "detected_at"
            ])
            st.dataframe(df_alerts, use_container_width=True)
        else:
            st.info("Sin alertas por ahora.")

    # ── Tab 5: Informes ───────────────────────────────────────────

    def _tab_reports(self) -> None:
        st.subheader("📈 Informes y Análisis")

        stats = intelligence_db.get_stats()

        # ── DB overview ───────────────────────────────────────────
        import plotly.express as px

        df_stats = pd.DataFrame([
            {"Tabla": k.replace("_", " ").title(), "Registros": v}
            for k, v in stats.items()
        ])
        fig = px.bar(
            df_stats, x="Registros", y="Tabla", orientation="h",
            title="Registros en base de datos",
            color="Registros",
            color_continuous_scale="Blues",
        )
        fig.update_layout(height=350, margin=dict(l=0, r=0, t=40, b=0), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        # ── Session history ───────────────────────────────────────
        st.markdown("### 📜 Historial de sesiones")
        sessions = intelligence_db.get_sessions(limit=50)
        if sessions:
            import plotly.express as px
            df_s = pd.DataFrame(sessions)
            if "task_type" in df_s.columns:
                tt_counts = df_s["task_type"].value_counts().reset_index()
                tt_counts.columns = ["Tipo", "Sesiones"]
                fig2 = px.pie(
                    tt_counts, values="Sesiones", names="Tipo",
                    title="Sesiones por tipo de tarea",
                )
                fig2.update_layout(height=280)
                st.plotly_chart(fig2, use_container_width=True)

            st.dataframe(
                _df(sessions, ["task_type", "query", "status", "created_at"]),
                use_container_width=True,
            )

        # ── Benchmark / gap analysis ──────────────────────────────
        st.markdown("### 🔬 Análisis de gaps y benchmarking")
        market_items = intelligence_db.get_market_intel(limit=500)
        if market_items:
            all_prods: List[Dict] = []
            for item in market_items:
                for prod in item.get("products", []):
                    all_prods.append({
                        "Empresa":   item.get("company", ""),
                        "Producto":  prod.get("name", "")[:80],
                        "Precio":    prod.get("price", ""),
                        "Categoría": item.get("category", ""),
                    })
            if all_prods:
                df_gp = pd.DataFrame(all_prods)
                st.markdown(f"**{len(df_gp)} productos catalogados de {df_gp['Empresa'].nunique()} empresas**")
                st.dataframe(df_gp, use_container_width=True, height=300)
        else:
            st.info("Ejecuta tareas de **market_intel** para generar análisis de competencia.")

        # ── Exports ───────────────────────────────────────────────
        st.divider()
        st.markdown("### 📦 Exportar datos")
        cols = st.columns(4)
        exports = [
            ("leads",               "👥 Leads"),
            ("market_intelligence", "📊 Market"),
            ("content_items",       "📰 Contenido"),
            ("crawl_sessions",      "🔄 Sesiones"),
        ]
        for col, (table, label) in zip(cols, exports):
            with col:
                col.download_button(
                    label=f"⬇️ {label}",
                    data=intelligence_db.export_json(table),
                    file_name=f"{table}_{datetime.now():%Y%m%d}.json",
                    mime="application/json",
                    key=f"export_{table}",
                )


# ── Entry point ───────────────────────────────────────────────────────────────

def render_market_intelligence_panel() -> None:
    MarketIntelligencePanel().render()
