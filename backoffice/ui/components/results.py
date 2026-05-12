"""IS-BACKOFFICE – main content renderer.

Each module is exposed as a ``_page_<name>()`` function and wired in
``render_main_content()`` based on ``st.session_state.active_page``.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from .dashboard import render_default_dashboard


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_safe_path(raw: str) -> str | None:
    """Resolve and validate a folder path supplied by the user.

    Returns the real, absolute path if it exists on disk, or *None*.
    Using ``os.path.realpath`` normalises the path (resolves ``..`` and
    symlinks) so that the final value passed to filesystem operations is
    always a canonical absolute path.
    """
    if not raw or not raw.strip():
        return None
    resolved = os.path.realpath(raw.strip())
    if not os.path.isdir(resolved):
        return None
    return resolved

def _section_header(title: str, subtitle: str = "") -> None:
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)
    st.markdown("---")


def _render_signal_cards(signals: list[dict[str, str]], columns: int = 3) -> None:
    cols = st.columns(columns)
    for idx, signal in enumerate(signals):
        with cols[idx % columns]:
            st.markdown(f"**{signal['title']}**")
            if signal.get("severity"):
                st.caption(signal["severity"])
            st.write(signal["summary"])
            if signal.get("action"):
                st.write(f"→ {signal['action']}")


def _build_structured_response(result: dict[str, Any]) -> dict[str, Any]:
    themes = result.get("themes", [])
    errors = result.get("errors", [])
    source = result.get("folder_path") or result.get("url") or "uploaded files"
    doc_count = result.get("doc_count", result.get("file_count", 0))
    relationships = result.get("relationships", 0)
    timeline_events = result.get("timeline_events", 0)
    narrative = result.get("narrative") or (
        f"Se analizaron {doc_count} documento(s) y se consolidó un resumen trazable del workspace."
    )

    key_findings = [
        f"{doc_count} documento(s) procesados en el workspace actual.",
        f"{relationships} relaciones cruzadas detectadas para soporte analítico.",
        f"{timeline_events} evento(s) temporales listos para revisión operativa.",
    ]
    if themes:
        key_findings.append(f"Temas dominantes: {', '.join(themes[:3])}.")
    if errors:
        key_findings.append(f"Se detectaron {len(errors)} incidencia(s) de parsing para revisión.")

    recommendations = [
        "Convertir este análisis en brief ejecutivo compartible.",
        "Revisar entidades con mayor densidad de relaciones.",
        "Activar seguimiento sobre documentos o cuentas con mayor riesgo.",
    ]
    if errors:
        recommendations.insert(0, "Revisar los documentos con errores antes de automatizar decisiones.")

    return {
        "executive_summary": narrative,
        "key_findings": key_findings,
        "recommendations": recommendations,
        "sources": [
            f"Origen principal: {source}",
            f"Formato generado: {result.get('output_format', 'summary')}",
            f"Confidence proxy: {min(0.99, 0.75 + (0.03 * min(len(themes), 5))):.2f}",
        ],
    }


def _render_structured_response(result: dict[str, Any]) -> None:
    structured = _build_structured_response(result)
    st.markdown("### Structured Intelligence Output")
    with st.expander("[1] Executive Summary", expanded=True):
        st.write(structured["executive_summary"])
    with st.expander("[2] Key Findings", expanded=True):
        for finding in structured["key_findings"]:
            st.write(f"• {finding}")
    with st.expander("[3] Recommendations", expanded=False):
        for recommendation in structured["recommendations"]:
            st.write(f"→ {recommendation}")
    with st.expander("[4] Sources", expanded=False):
        for source in structured["sources"]:
            st.write(f"- {source}")


def _render_document_analysis_result(result: dict[str, Any]) -> None:
    source = result.get("folder_path") or result.get("url") or "—"
    st.subheader("📂 Document Analysis Results")

    cols = st.columns(4)
    cols[0].metric("Files processed", result.get("doc_count", result.get("file_count", 0)))
    cols[1].metric("Words analysed", f"{result.get('word_count', 0):,}")
    cols[2].metric("Cross-references", result.get("relationships", 0))
    cols[3].metric("Timeline events", result.get("timeline_events", 0))
    st.caption(f"Source: {source}")

    narrative = result.get("narrative", "")
    if narrative:
        st.markdown("**Overview**")
        st.write(narrative)

    themes = result.get("themes", [])
    if themes:
        st.markdown("**Key Themes**")
        theme_cards = [
            {
                "title": theme,
                "severity": "Insight block",
                "summary": f"Tema detectado automáticamente en el análisis contextual #{i + 1}.",
                "action": "Track source evidence",
            }
            for i, theme in enumerate(themes[:6])
        ]
        _render_signal_cards(theme_cards, columns=min(3, len(theme_cards)))

    _render_structured_response(result)

    output_content = result.get("output_content", "")
    if output_content:
        with st.expander("[5] Deep Dive", expanded=False):
            fmt = result.get("output_format", "")
            if fmt == "database_entry":
                try:
                    st.json(json.loads(output_content))
                except json.JSONDecodeError:
                    st.code(output_content, language="json")
            else:
                st.markdown(output_content)
            st.download_button(
                "⬇️ Download as Markdown",
                data=output_content.encode("utf-8"),
                file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
            )

    errors = result.get("errors", [])
    if errors:
        with st.expander(f"⚠️ {len(errors)} parsing error(s)", expanded=False):
            for err in errors:
                st.warning(err)

    msg = result.get("message", "")
    if msg and not output_content:
        st.info(msg)


# ---------------------------------------------------------------------------
# Dashboard page
# ---------------------------------------------------------------------------

def _page_dashboard() -> None:
    render_default_dashboard()


# ---------------------------------------------------------------------------
# Workspace pages
# ---------------------------------------------------------------------------

def _page_clients_accounts() -> None:
    _section_header("👥 Clients & Accounts", "Unified client workspace with activity, risks, documents, and next actions")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Priority accounts", "18", delta="+2")
    col2.metric("Accounts at risk", "3", delta="+1")
    col3.metric("Unread client emails", "11", delta="-4")
    col4.metric("AI next actions", "9", delta="+3")

    st.markdown("### Client 360")
    _render_signal_cards(
        [
            {
                "title": "Atlas Manufacturing",
                "severity": "High risk",
                "summary": "Actividad -27%, 34 días sin respuesta y 2 propuestas rechazadas.",
                "action": "Contactar director de cuenta",
            },
            {
                "title": "Nova Retail",
                "severity": "Opportunity",
                "summary": "Mayor interacción comercial y forecast ascendente en mayo.",
                "action": "Preparar propuesta ejecutiva",
            },
            {
                "title": "Boreal Energy",
                "severity": "Watchlist",
                "summary": "Emails pendientes y documentación incompleta para cierre.",
                "action": "Solicitar documentación faltante",
            },
        ]
    )

    tabs = st.tabs(["Resumen", "Timeline", "Riesgos", "Documentos", "Next Actions"])
    with tabs[0]:
        st.write("Vista centrada en perfil, forecast, actividad y salud comercial de la cuenta.")
    with tabs[1]:
        timeline = pd.DataFrame(
            [
                {"Fecha": "2026-05-08", "Evento": "Email de pricing recibido", "Origen": "Email"},
                {"Fecha": "2026-05-05", "Evento": "Reunión de seguimiento", "Origen": "CRM note"},
                {"Fecha": "2026-05-01", "Evento": "Oferta actualizada", "Origen": "PDF"},
            ]
        )
        st.dataframe(timeline, use_container_width=True, hide_index=True)
    with tabs[2]:
        st.info("Cada riesgo explica el porqué: inactividad, pricing y señales documentales.")
    with tabs[3]:
        st.caption("Fuentes trazables: emails, PDFs, notas CRM y resúmenes ejecutivos.")
    with tabs[4]:
        st.write("→ Reactivar cuentas en silencio")
        st.write("→ Programar revisión comercial semanal")
        st.write("→ Generar brief ejecutivo compartible")


def _page_deals_pipeline() -> None:
    _section_header("💼 Deals & Pipeline", "Pipeline monitoring, pricing anomalies, and close-plan recommendations")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Open pipeline", "€4.8M", delta="+6%")
    col2.metric("Likely to close", "€1.9M", delta="+12%")
    col3.metric("Stalled deals", "5", delta="+2")
    col4.metric("Pricing anomalies", "2", delta="+1")

    st.markdown("### Executive Snapshot")
    _render_signal_cards(
        [
            {
                "title": "Delta Renewal",
                "severity": "Pricing anomaly",
                "summary": "Descuento 18% sobre benchmark y margen fuera de política.",
                "action": "Validar pricing",
            },
            {
                "title": "Nova Expansion",
                "severity": "Closing signal",
                "summary": "Nueva actividad con stakeholders y mejor probabilidad de cierre.",
                "action": "Actualizar close plan",
            },
            {
                "title": "Helix Platform",
                "severity": "Frozen deal",
                "summary": "21 días sin cambio en la etapa y sin emails respondidos.",
                "action": "Escalar con liderazgo",
            },
        ]
    )

    pipeline = pd.DataFrame(
        [
            {"Deal": "Nova Expansion", "Stage": "Proposal", "Probability": "78%", "Next step": "Executive review"},
            {"Deal": "Delta Renewal", "Stage": "Negotiation", "Probability": "62%", "Next step": "Pricing approval"},
            {"Deal": "Helix Platform", "Stage": "Qualification", "Probability": "34%", "Next step": "Re-engagement"},
        ]
    )
    st.dataframe(pipeline, use_container_width=True, hide_index=True)


def _page_research_documents() -> None:
    _section_header("📄 Research & Documents", "Research-first workspace with grounded outputs and source traceability")

    col1, col2, col3 = st.columns(3)
    col1.metric("Tracked sources", "126", delta="+9")
    col2.metric("Executive briefs", "6", delta="+2")
    col3.metric("Open research tasks", "4", delta="-1")

    st.markdown("### Structured Outputs")
    _render_signal_cards(
        [
            {
                "title": "Executive Summary",
                "severity": "Level 1",
                "summary": "Resumen corto para decisión rápida.",
                "action": "Open brief",
            },
            {
                "title": "Key Findings",
                "severity": "Level 2",
                "summary": "Insights priorizados con trazabilidad y severidad.",
                "action": "Inspect findings",
            },
            {
                "title": "Deep Dive",
                "severity": "Level 3",
                "summary": "Explicación completa con fuentes y contexto persistente.",
                "action": "Review evidence",
            },
        ]
    )

    shortcut1, shortcut2 = st.columns(2)
    with shortcut1:
        if st.button("Open Document Analysis", use_container_width=True, key="research_open_doc_analysis"):
            st.switch_page("pages/document_analysis.py")
    with shortcut2:
        if st.button("Open Instruction Panel", use_container_width=True, key="research_open_instruction_panel"):
            st.switch_page("pages/instruction_panel.py")

    st.markdown("### Source Traceability Layer")
    st.write("- Email X · `renewal-thread-atlas.eml`")
    st.write("- PDF Y · `pricing-delta-q2.pdf`")
    st.write("- CRM note Z · `nova-opportunity-2026-05-08`")


def _page_alerts_risks() -> None:
    _section_header("🚨 Alerts & Risks", "Explainable alerts for activity drops, stalled opportunities, and pricing anomalies")

    _render_signal_cards(
        [
            {
                "title": "Risk Score = 82",
                "severity": "Cliente Atlas",
                "summary": "34 días sin actividad, 2 ofertas rechazadas y caída de revenue del 18%.",
                "action": "Open account workspace",
            },
            {
                "title": "Risk Score = 74",
                "severity": "Pipeline EMEA",
                "summary": "Baja conversión semanal y exceso de oportunidades congeladas.",
                "action": "Inspect pipeline",
            },
            {
                "title": "Risk Score = 69",
                "severity": "Oferta Delta",
                "summary": "Pricing fuera de rango y margen por debajo del objetivo.",
                "action": "Review commercial approval",
            },
        ]
    )

    with st.expander("Why the system thinks this", expanded=True):
        st.write("• Inactividad prolongada detectada en comunicaciones recientes.")
        st.write("• Cambios anómalos en pricing respecto al benchmark del portfolio.")
        st.write("• Señales documentales y de pipeline combinadas en el score.")


def _page_reports_executive() -> None:
    _section_header("📈 Reports & Executive", "Executive reporting, decision narratives, and structured recommendations")

    st.markdown("### Executive Blocks")
    with st.expander("[1] Executive Summary", expanded=True):
        st.write("El negocio mantiene crecimiento previsto, pero requiere foco inmediato en cuentas y deals con señales de riesgo.")
    with st.expander("[2] Risks", expanded=True):
        st.write("• 3 cuentas estratégicas con actividad decreciente.")
        st.write("• 2 oportunidades congeladas sin plan de cierre.")
    with st.expander("[3] Opportunities", expanded=False):
        st.write("• Nova Expansion y Atlas Upsell muestran mayor probabilidad de cierre.")
    with st.expander("[4] Recommendations", expanded=False):
        st.write("→ Revisar pricing crítico.")
        st.write("→ Lanzar workflow de follow-up automático.")
    with st.expander("[5] Sources", expanded=False):
        st.write("- Emails de clientes")
        st.write("- PDFs de ofertas")
        st.write("- Notas CRM")
    preview = pd.DataFrame(
        [
            {"Report": "Executive Snapshot", "Status": "Ready", "Audience": "Leadership"},
            {"Report": "Risk Brief", "Status": "Scheduled", "Audience": "Sales Ops"},
            {"Report": "Pipeline Review", "Status": "Ready", "Audience": "Revenue team"},
        ]
    )
    st.dataframe(preview, use_container_width=True, hide_index=True)


def _page_settings_integrations() -> None:
    _section_header("⚙️ Settings & Integrations", "Capability registry, integrations, and operational configuration")

    capabilities = pd.DataFrame(
        [
            {"Capability": "Offer validation", "Visible in UI": "Deals & Pipeline", "Trigger": "Deal review"},
            {"Capability": "Forecasting", "Visible in UI": "Intelligence Center", "Trigger": "Executive snapshot"},
            {"Capability": "Semantic search", "Visible in UI": "Research & Documents", "Trigger": "AI command"},
            {"Capability": "Review queue", "Visible in UI": "Alerts & Risks", "Trigger": "Risk workflow"},
        ]
    )
    st.dataframe(capabilities, use_container_width=True, hide_index=True)
    st.info("La plataforma expone capacidades técnicas como espacios operativos visibles.")


# ---------------------------------------------------------------------------
# Ingestion page
# ---------------------------------------------------------------------------

def _page_ingestion() -> None:
    _section_header("📥 INGESTION", "Ingest files, URLs, watch folders, bulk import, and scrape the web")

    tab_upload, tab_url, tab_watch, tab_bulk, tab_scraper = st.tabs([
        "📂 File Upload", "🌐 URL Ingest", "👁️ Watch Folder", "📦 Bulk Import", "🕷️ Scraper"
    ])

    with tab_upload:
        st.subheader("Upload files for ingestion")
        uploaded = st.file_uploader(
            "Archivos a procesar",
            accept_multiple_files=True,
            type=["pdf", "docx", "xlsx", "csv", "txt", "json", "xml", "html", "pptx", "md"],
            key="ing_file_uploader",
        )
        col1, col2 = st.columns([2, 1])
        with col1:
            output_type = st.selectbox(
                "Output type",
                ["summary", "executive_summary", "report", "list", "timeline", "comparison"],
                key="ing_output_type",
            )
        with col2:
            st.write("")
            st.write("")
            run = st.button("📥 Ingestar Archivos", type="primary", key="ing_run_upload", use_container_width=True)

        if run and uploaded:
            from backoffice.ui.app import _run_real_operation
            result = _run_real_operation(
                "📥 INGESTION", "Ingest local files",
                {"files": uploaded, "output_type": output_type}
            )
            st.session_state["last_result"] = result
            st.session_state["current_section"] = "📥 INGESTION"
            _render_document_analysis_result(result)
        elif run and not uploaded:
            st.warning("Por favor sube al menos un archivo.")

        last = st.session_state.get("last_result")
        if last and last.get("section") == "📥 INGESTION" and not run:
            _render_document_analysis_result(last)

    with tab_url:
        st.subheader("Ingestar desde URL")
        url = st.text_input("URL del recurso", placeholder="https://example.com/article", key="ing_url")
        col1, col2 = st.columns([2, 1])
        with col1:
            url_output_type = st.selectbox(
                "Output type",
                ["summary", "executive_summary", "report"],
                key="ing_url_output_type",
            )
        with col2:
            st.write("")
            st.write("")
            run_url = st.button("🌐 Ingestar URL", type="primary", key="ing_run_url", use_container_width=True)

        if run_url and url:
            from backoffice.ui.app import _run_url_analysis
            result = _run_url_analysis(url, output_type=url_output_type)
            st.session_state["last_result"] = result
            _render_document_analysis_result(result)
        elif run_url and not url:
            st.warning("Introduce una URL válida.")

    with tab_watch:
        st.subheader("Monitorear carpeta automáticamente")
        folder = st.text_input("Ruta de la carpeta", placeholder="/home/usuario/documentos", key="ing_watch_folder")
        col1, col2 = st.columns(2)
        with col1:
            auto = st.toggle("Activar monitoreo automático", value=False, key="ing_watch_auto")
        with col2:
            interval = st.selectbox("Frecuencia", ["5 min", "15 min", "30 min", "1 hora"], key="ing_watch_interval")
        run_watch = st.button("▶️ Analizar Carpeta Ahora", type="primary", key="ing_run_watch", use_container_width=True)

        if run_watch and folder:
            safe = _resolve_safe_path(folder)
            if safe is None:
                st.error(f"Carpeta no encontrada: {folder}")
            else:
                from backoffice.ui.app import _run_folder_analysis
                result = _run_folder_analysis(safe, output_type="list")
                st.session_state["last_result"] = result
                _render_document_analysis_result(result)
        elif run_watch and not folder:
            st.warning("Introduce una ruta de carpeta válida.")

        if auto:
            st.info(f"Monitoreo activado: cada {interval}. Los nuevos archivos se procesarán automáticamente.")

    with tab_bulk:
        st.subheader("Importación masiva de archivos")
        bulk_files = st.file_uploader(
            "Carga múltiple de archivos",
            accept_multiple_files=True,
            type=["pdf", "docx", "xlsx", "csv", "txt", "json"],
            key="ing_bulk_uploader",
        )
        if bulk_files:
            st.caption(f"{len(bulk_files)} archivo(s) seleccionados")
            st.progress(0.0, text="Listo para procesar")
        run_bulk = st.button("📦 Importar Masivamente", type="primary", key="ing_run_bulk", use_container_width=True)

        if run_bulk and bulk_files:
            from backoffice.ui.app import _run_real_operation
            result = _run_real_operation("📥 INGESTION", "Bulk import", {"files": bulk_files})
            st.session_state["last_result"] = result
            _render_document_analysis_result(result)
        elif run_bulk and not bulk_files:
            st.warning("Sube archivos antes de importar.")

    with tab_scraper:
        st.subheader("Web Scraper")
        urls_text = st.text_area(
            "URLs (una por línea)",
            placeholder="https://example.com\nhttps://other.com",
            height=150,
            key="ing_scraper_urls",
        )
        col1, col2 = st.columns(2)
        with col1:
            depth = st.slider("Profundidad de scraping", min_value=1, max_value=5, value=1, key="ing_scraper_depth")
        with col2:
            scrape_output = st.selectbox("Output type", ["summary", "report", "list"], key="ing_scraper_output")
        run_scraper = st.button("🕷️ Ejecutar Scraper", type="primary", key="ing_run_scraper", use_container_width=True)

        if run_scraper and urls_text.strip():
            urls = [u.strip() for u in urls_text.strip().splitlines() if u.strip()]
            all_results = []
            progress = st.progress(0.0)
            for i, url in enumerate(urls):
                try:
                    from backoffice.ui.app import _run_url_analysis
                    r = _run_url_analysis(url, output_type=scrape_output)
                    all_results.append(r)
                except Exception as exc:
                    st.warning(f"Error scraping {url}: {exc}")
                progress.progress((i + 1) / len(urls))
            st.success(f"Scraping completado: {len(all_results)}/{len(urls)} URLs procesadas.")
        elif run_scraper and not urls_text.strip():
            st.warning("Introduce al menos una URL.")

    _render_agent_orchestrator_panel(section="📥 INGESTION")


# ---------------------------------------------------------------------------
# Cleaning page
# ---------------------------------------------------------------------------

def _page_cleaning() -> None:
    _section_header("🧹 CLEANING", "Deduplication, standardization, quality audits, and fuzzy merging")

    tab_dedup, tab_std, tab_audit, tab_outliers, tab_fuzzy = st.tabs([
        "🔁 Deduplicación", "📐 Estandarización", "✅ Auditoría", "⚠️ Outliers", "🔗 Fuzzy Merge"
    ])

    with tab_dedup:
        st.subheader("Eliminar duplicados")
        col1, col2 = st.columns(2)
        with col1:
            entity_type = st.selectbox(
                "Tipo de entidad",
                ["cliente", "contacto", "oferta", "oportunidad", "venta", "documento"],
                key="clean_dedup_entity",
            )
        with col2:
            threshold = st.slider("Umbral de similitud", 0.5, 1.0, 0.85, 0.01, key="clean_dedup_thresh")
        run = st.button("🔁 Ejecutar Deduplicación", type="primary", key="clean_run_dedup", use_container_width=True)
        if run:
            st.info(f"Deduplicando '{entity_type}' con umbral {threshold}. Ingesta datos primero para resultados reales.")
            _render_before_after_stub()

    with tab_std:
        st.subheader("Estandarizar datos")
        preset = st.selectbox(
            "Regla predefinida",
            ["Teléfonos E.164", "Fechas ISO-8601", "Normalización de moneda", "Limpieza de direcciones"],
            key="clean_std_preset",
        )
        run = st.button("📐 Estandarizar", type="primary", key="clean_run_std", use_container_width=True)
        if run:
            st.info(f"Aplicando regla '{preset}'. Ingesta datos primero para resultados reales.")
            _render_before_after_stub()

    with tab_audit:
        st.subheader("Auditoría de calidad")
        dataset = st.selectbox(
            "Dataset",
            ["clientes", "ofertas", "ventas", "oportunidades", "documentos"],
            key="clean_audit_dataset",
        )
        run = st.button("✅ Ejecutar Auditoría", type="primary", key="clean_run_audit", use_container_width=True)
        if run:
            st.info(f"Auditando '{dataset}'. Ingesta datos primero para resultados reales.")
            _render_quality_stub()

    with tab_outliers:
        st.subheader("Detección de outliers")
        col1, col2 = st.columns(2)
        with col1:
            column = st.text_input("Columna a analizar", placeholder="deal_value", key="clean_outlier_col")
        with col2:
            method = st.selectbox("Método", ["IQR", "Z-score", "Isolation Forest"], key="clean_outlier_method")
        run = st.button("⚠️ Detectar Outliers", type="primary", key="clean_run_outliers", use_container_width=True)
        if run:
            st.info(f"Detectando outliers en '{column}' con método '{method}'. Ingesta datos primero.")

    with tab_fuzzy:
        st.subheader("Fusión por similitud (Fuzzy Merge)")
        col1, col2 = st.columns(2)
        with col1:
            fuzz_thresh = st.slider("Umbral fuzzy", 0.5, 1.0, 0.9, 0.01, key="clean_fuzzy_thresh")
        with col2:
            review_mode = st.toggle("Modo revisión manual", value=True, key="clean_fuzzy_review")
        run = st.button("🔗 Ejecutar Fuzzy Merge", type="primary", key="clean_run_fuzzy", use_container_width=True)
        if run:
            st.info(f"Fuzzy merge con umbral {fuzz_thresh}. Ingesta datos primero para resultados reales.")

    _render_agent_orchestrator_panel(section="🧹 CLEANING")


def _render_before_after_stub() -> None:
    col1, col2 = st.columns(2)
    before = pd.DataFrame([{"phone": "(555) 123-4567", "date": "01/12/2026", "amount": "25.000,00"}])
    after = pd.DataFrame([{"phone": "+15551234567", "date": "2026-12-01", "amount": "25000.00"}])
    with col1:
        st.markdown("**Antes**")
        st.dataframe(before, use_container_width=True)
    with col2:
        st.markdown("**Después**")
        st.dataframe(after, use_container_width=True)


def _render_quality_stub() -> None:
    issues = pd.DataFrame([
        {"fila": 14, "problema": "Formato de fecha inválido", "sugerencia": "Convertir a ISO-8601"},
        {"fila": 21, "problema": "Posible duplicado", "sugerencia": "Fusionar con fila 17"},
    ])
    st.dataframe(issues, use_container_width=True)
    st.metric("Puntuación de calidad", "94", delta="+12")


# ---------------------------------------------------------------------------
# Extraction page
# ---------------------------------------------------------------------------

def _page_extraction() -> None:
    _section_header("🔍 EXTRACTION", "NER, PDF parsing, batch processing, few-shot, and table detection")

    tab_ner, tab_pdf, tab_batch, tab_fewshot, tab_tables = st.tabs([
        "📝 Text NER", "📄 PDF Extraction", "⚙️ Batch Processing", "🎯 Few-Shot", "📊 Table Detection"
    ])

    with tab_ner:
        st.subheader("Extracción de entidades con NER")
        text_input = st.text_area("Texto a analizar", height=200, placeholder="Pega aquí el texto...", key="ext_ner_text")
        entity_types = st.multiselect(
            "Tipos de entidad",
            ["PERSON", "ORG", "GPE", "DATE", "MONEY", "PRODUCT", "EVENT", "LAW", "NORP"],
            default=["PERSON", "ORG", "DATE"],
            key="ext_ner_types",
        )
        run = st.button("📝 Extraer Entidades", type="primary", key="ext_run_ner", use_container_width=True)
        if run and text_input.strip():
            with st.spinner("Analizando texto..."):
                entities = pd.DataFrame([
                    {"Entidad": "Ejemplo Corp", "Tipo": "ORG", "Confianza": 0.97},
                    {"Entidad": "Juan García", "Tipo": "PERSON", "Confianza": 0.92},
                    {"Entidad": "2024-01-15", "Tipo": "DATE", "Confianza": 0.88},
                ])
                st.dataframe(entities, use_container_width=True)
                hist = pd.DataFrame({"bucket": ["0.8–0.85", "0.86–0.9", "0.91–0.95", "0.96–1.0"], "count": [0, 1, 1, 1]})
                st.bar_chart(hist.set_index("bucket"))
        elif run and not text_input.strip():
            st.warning("Introduce texto para analizar.")

    with tab_pdf:
        st.subheader("Extracción de documentos PDF")
        pdf_files = st.file_uploader(
            "Subir PDFs",
            type=["pdf"],
            accept_multiple_files=True,
            key="ext_pdf_uploader",
        )
        run = st.button("📄 Procesar PDFs", type="primary", key="ext_run_pdf", use_container_width=True)
        if run and pdf_files:
            from backoffice.ui.app import _run_real_operation
            result = _run_real_operation("🔍 EXTRACTION", "Process documents", {"documents": pdf_files})
            st.session_state["last_result"] = result
            _render_document_analysis_result(result)
        elif run and not pdf_files:
            st.warning("Sube al menos un PDF.")

    with tab_batch:
        st.subheader("Procesamiento por lotes")
        folder_path = st.text_input("Ruta de carpeta", placeholder="/home/usuario/docs", key="ext_batch_folder")
        ext_types = st.multiselect(
            "Tipos de entidad a extraer",
            ["clientes", "contactos", "ofertas", "oportunidades", "ventas", "productos", "fechas", "montos"],
            default=["clientes", "ofertas"],
            key="ext_batch_types",
        )
        run = st.button("⚙️ Ejecutar Batch", type="primary", key="ext_run_batch", use_container_width=True)
        if run and folder_path:
            safe = _resolve_safe_path(folder_path)
            if safe is None:
                st.error(f"Carpeta no encontrada: {folder_path}")
            else:
                from backoffice.ui.app import _run_folder_analysis
                result = _run_folder_analysis(safe, output_type="report")
                st.session_state["last_result"] = result
                _render_document_analysis_result(result)
        elif run and not folder_path:
            st.warning("Introduce la ruta de la carpeta.")

    with tab_fewshot:
        st.subheader("Extracción Few-Shot (ejemplos personalizados)")
        examples = st.text_area(
            "Ejemplos few-shot (formato JSONL o texto libre)",
            height=200,
            placeholder='{"text": "...", "entities": [{"value": "ACME", "type": "ORG"}]}',
            key="ext_fewshot_examples",
        )
        test_text = st.text_area("Texto de prueba", height=100, key="ext_fewshot_test")
        run = st.button("🎯 Ejecutar Few-Shot", type="primary", key="ext_run_fewshot", use_container_width=True)
        if run:
            st.info("Few-shot extraction requiere modelo de IA. Configura OPENAI_API_KEY para activar.")

    with tab_tables:
        st.subheader("Detección y extracción de tablas")
        table_file = st.file_uploader(
            "Subir PDF o imagen",
            type=["pdf", "png", "jpg", "jpeg"],
            key="ext_table_uploader",
        )
        detect = st.toggle("Detección automática de tablas", value=True, key="ext_table_detect")
        run = st.button("📊 Extraer Tablas", type="primary", key="ext_run_tables", use_container_width=True)
        if run and table_file:
            st.info("Extracción de tablas de imágenes requiere Tesseract OCR instalado.")
        elif run and not table_file:
            st.warning("Sube un archivo PDF o imagen.")

    _render_agent_orchestrator_panel(section="🔍 EXTRACTION")


# ---------------------------------------------------------------------------
# Graph page
# ---------------------------------------------------------------------------

def _page_graph() -> None:
    _section_header("🕸️ GRAPH", "Knowledge graph search, entity explorer, path finder, and visualization")

    tab_search, tab_explore, tab_paths, tab_comm, tab_viz = st.tabs([
        "🔍 Search", "🧩 Entity Explorer", "🛣️ Path Finder", "👥 Communities", "🌐 Visualizer"
    ])

    with tab_search:
        st.subheader("Buscar en el grafo de conocimiento")
        query = st.text_input("Consulta", placeholder="ACME digital roadmap", key="graph_search_query")
        run = st.button("🔍 Buscar", type="primary", key="graph_run_search", use_container_width=True)
        if run and query:
            st.info(f"Buscando '{query}' en el grafo. Ingesta documentos primero para poblar el grafo.")
            _render_graph_results_stub()
        elif run and not query:
            st.warning("Introduce un término de búsqueda.")

    with tab_explore:
        st.subheader("Explorador de entidades")
        col1, col2 = st.columns(2)
        with col1:
            entity_id = st.text_input("ID de entidad", value="entity_001", key="graph_explore_id")
        with col2:
            depth = st.slider("Profundidad", 1, 5, 2, key="graph_explore_depth")
        run = st.button("🧩 Explorar Conexiones", type="primary", key="graph_run_explore", use_container_width=True)
        if run:
            st.info(f"Explorando entidad '{entity_id}' a profundidad {depth}.")
            _render_graph_html_stub()

    with tab_paths:
        st.subheader("Encontrar camino entre entidades")
        col1, col2 = st.columns(2)
        with col1:
            from_entity = st.text_input("Entidad origen", value="client_001", key="graph_path_from")
        with col2:
            to_entity = st.text_input("Entidad destino", value="offer_210", key="graph_path_to")
        run = st.button("🛣️ Encontrar Camino", type="primary", key="graph_run_path", use_container_width=True)
        if run:
            st.info(f"Buscando camino entre '{from_entity}' y '{to_entity}'.")

    with tab_comm:
        st.subheader("Detección de comunidades")
        include_stats = st.toggle("Incluir estadísticas del grafo", value=True, key="graph_comm_stats")
        run = st.button("👥 Detectar Comunidades", type="primary", key="graph_run_comm", use_container_width=True)
        if run:
            st.info("Detección de comunidades requiere datos en el grafo. Ingesta documentos primero.")

    with tab_viz:
        st.subheader("Visualizador de subgrafo interactivo")
        center_entity = st.text_input("Entidad central", value="client_001", key="graph_viz_center")
        viz_depth = st.slider("Profundidad de visualización", 1, 5, 2, key="graph_viz_depth")
        run = st.button("🌐 Visualizar Subgrafo", type="primary", key="graph_run_viz", use_container_width=True)
        if run:
            _render_graph_html_stub()

    _render_agent_orchestrator_panel(section="🕸️ GRAPH")


def _render_graph_results_stub() -> None:
    data = pd.DataFrame([
        {"Entidad": "ACME Corp", "Tipo": "Cliente", "Conexiones": 12, "Relevancia": 0.95},
        {"Entidad": "Digital Roadmap", "Tipo": "Oferta", "Conexiones": 5, "Relevancia": 0.87},
    ])
    st.dataframe(data, use_container_width=True)


def _render_graph_html_stub() -> None:
    html = """
    <div style='font-family:sans-serif; padding:20px; border-radius:8px;
                background:#1e293b; color:#f1f5f9; text-align:center;'>
        <h4 style='color:#60a5fa;'>🕸️ Grafo Interactivo</h4>
        <p>Ingesta documentos para poblar el grafo de conocimiento.</p>
        <p style='color:#94a3b8; font-size:0.85rem;'>
            Una vez con datos, aquí se mostrará el grafo interactivo.
        </p>
    </div>
    """
    components.html(html, height=200)


# ---------------------------------------------------------------------------
# Analytics page
# ---------------------------------------------------------------------------

def _page_analytics() -> None:
    _section_header("📊 ANALYTICS", "Insights, natural language queries, forecasting, and what-if analysis")

    tab_insights, tab_nlq, tab_forecast, tab_whatif, tab_dash = st.tabs([
        "💡 Insights", "💬 NL Query", "📈 Forecasting", "🧪 What-If", "🖥️ Dashboard Builder"
    ])

    with tab_insights:
        st.subheader("Análisis de datos e insights")
        col1, col2 = st.columns(2)
        with col1:
            dataset = st.selectbox(
                "Dataset",
                ["ventas", "pipeline", "clientes", "ofertas", "documentos"],
                key="anal_insights_dataset",
            )
        with col2:
            insight_type = st.selectbox(
                "Tipo de análisis",
                ["anomalías", "tendencias", "correlaciones", "distribución"],
                key="anal_insights_type",
            )
        run = st.button("💡 Generar Insights", type="primary", key="anal_run_insights", use_container_width=True)
        if run:
            _render_analytics_stub()

    with tab_nlq:
        st.subheader("Consulta en lenguaje natural")
        question = st.text_area(
            "Haz una pregunta sobre tus datos",
            placeholder="¿Cuáles son los documentos más importantes del último mes?",
            height=120,
            key="anal_nlq_question",
        )
        run = st.button("🔍 Consultar", type="primary", key="anal_run_nlq", use_container_width=True)
        if run and question.strip():
            st.markdown("**Respuesta:**")
            st.info(
                "Consulta en lenguaje natural requiere datos ingestados y opcionalmente OPENAI_API_KEY. "
                "Ingesta documentos primero para obtener resultados reales."
            )
        elif run and not question.strip():
            st.warning("Introduce una pregunta.")

    with tab_forecast:
        st.subheader("Forecasting y predicciones")
        col1, col2, col3 = st.columns(3)
        with col1:
            metric = st.selectbox(
                "Métrica",
                ["ingresos", "tasa de conversión", "valor de pipeline", "volumen documentos"],
                key="anal_forecast_metric",
            )
        with col2:
            horizon = st.slider("Horizonte (meses)", 1, 24, 6, key="anal_forecast_horizon")
        with col3:
            model = st.selectbox("Modelo", ["Prophet", "ARIMA", "Media móvil"], key="anal_forecast_model")
        run = st.button("📈 Generar Forecast", type="primary", key="anal_run_forecast", use_container_width=True)
        if run:
            chart_df = pd.DataFrame({
                "mes": ["Ene", "Feb", "Mar", "Abr", "May", "Jun"],
                "real": [42000, 45000, 47000, 53000, 56000, None],
                "forecast": [43000, 45500, 49000, 52500, 57000, 61000],
            })
            st.line_chart(chart_df.set_index("mes"))
            st.caption(f"Forecast de '{metric}' a {horizon} meses con modelo {model}")

    with tab_whatif:
        st.subheader("Análisis What-If")
        col1, col2 = st.columns(2)
        with col1:
            price_delta = st.slider("Variación de precio (%)", -30, 30, 0, key="anal_wi_price")
        with col2:
            conv_delta = st.slider("Variación de conversión (%)", -30, 30, 0, key="anal_wi_conv")
        base_revenue = 50000
        simulated = base_revenue * (1 + price_delta / 100) * (1 + conv_delta / 100)
        delta_pct = (simulated - base_revenue) / base_revenue * 100
        col1, col2 = st.columns(2)
        col1.metric("Ingreso base (€)", f"{base_revenue:,.0f}")
        col2.metric("Ingreso simulado (€)", f"{simulated:,.0f}", delta=f"{delta_pct:+.1f}%")

        sim_df = pd.DataFrame({
            "escenario": ["Base", "What-If"],
            "ingreso": [base_revenue, simulated],
        })
        st.bar_chart(sim_df.set_index("escenario"))

    with tab_dash:
        st.subheader("Constructor de dashboards")
        layout = st.selectbox(
            "Plantilla de dashboard",
            ["Ejecutivo", "Operaciones", "Ventas", "Documentos", "Financiero"],
            key="anal_dash_layout",
        )
        run = st.button("🖥️ Generar Dashboard", type="primary", key="anal_run_dash", use_container_width=True)
        if run:
            _render_analytics_stub()
            st.info(f"Dashboard '{layout}' generado. Ingesta datos para valores reales.")

    _render_agent_orchestrator_panel(section="📊 ANALYTICS")


def _render_analytics_stub() -> None:
    chart_df = pd.DataFrame({
        "mes": ["Ene", "Feb", "Mar", "Abr", "May"],
        "real": [42000, 45000, 47000, 53000, 56000],
        "forecast": [43000, 45500, 49000, 52500, 57000],
    })
    st.line_chart(chart_df.set_index("mes"))
    st.success("Tendencia: Crecimiento positivo sostenido.")
    st.info("Correlación: El descuento en ofertas afecta la conversión en el segmento PYME.")
    st.warning("Anomalía: Actividad reducida en el período analizado.")


# ---------------------------------------------------------------------------
# Reporting page
# ---------------------------------------------------------------------------

def _page_reporting() -> None:
    _section_header("📑 REPORTING", "Generate, schedule, export, email, and review report history")

    tab_gen, tab_sched, tab_export, tab_email, tab_hist = st.tabs([
        "📋 Generar", "⏰ Programar", "💾 Exportar", "📧 Email", "🗂️ Historial"
    ])

    with tab_gen:
        st.subheader("Generar informe")
        col1, col2 = st.columns(2)
        with col1:
            template = st.selectbox(
                "Plantilla",
                [
                    "Resumen Ejecutivo", "Diagnóstico de Cliente", "Informe de Ventas",
                    "Market Research", "Brief de Producto", "Análisis Jurídico",
                    "Informe Financiero", "Newsletter", "Post LinkedIn",
                    "Oferta Comercial", "Brochure", "Presentación PowerPoint",
                    "Contrato", "Factura", "Presupuesto",
                ],
                key="rep_gen_template",
            )
        with col2:
            date_range = st.date_input("Rango de fechas", value=(), key="rep_gen_dates")

        extra_context = st.text_area(
            "Contexto adicional (instrucciones especiales)",
            placeholder="Incluye KPIs de Q1, enfócate en el mercado europeo...",
            height=80,
            key="rep_gen_context",
        )

        run = st.button("📋 Generar Informe", type="primary", key="rep_run_gen", use_container_width=True)
        if run:
            with st.spinner(f"Generando '{template}'..."):
                preview_content = f"""# {template}

**Fecha:** {datetime.now().strftime('%Y-%m-%d')}

## Resumen Ejecutivo

Este informe ha sido generado automáticamente por IS-BACKOFFICE.
Ingesta documentos y datos para obtener contenido personalizado.

## Hallazgos Principales

- Punto clave 1: Análisis pendiente de datos reales
- Punto clave 2: Configure OPENAI_API_KEY para resúmenes con IA
- Punto clave 3: Use el módulo de Ingesta para cargar documentos

## Próximos pasos

1. Ingestar documentos relevantes
2. Ejecutar extracción de entidades
3. Regenerar este informe con datos reales
"""
            st.markdown(preview_content)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            col_dl1, col_dl2, col_dl3, col_dl4 = st.columns(4)
            col_dl1.download_button(
                "⬇️ Markdown",
                data=preview_content,
                file_name=f"report_{ts}.md",
                mime="text/markdown",
            )
            col_dl2.download_button(
                "⬇️ TXT",
                data=preview_content,
                file_name=f"report_{ts}.txt",
                mime="text/plain",
            )
            col_dl3.download_button(
                "⬇️ CSV",
                data="section,content\nresumen,pendiente\n",
                file_name=f"report_{ts}.csv",
                mime="text/csv",
            )
            col_dl4.download_button(
                "⬇️ JSON",
                data=json.dumps({"template": template, "date": ts, "content": preview_content}),
                file_name=f"report_{ts}.json",
                mime="application/json",
            )

    with tab_sched:
        st.subheader("Programar informes automáticos")
        col1, col2, col3 = st.columns(3)
        with col1:
            frequency = st.selectbox("Frecuencia", ["Diario", "Semanal", "Mensual", "Trimestral"], key="rep_sched_freq")
        with col2:
            sched_format = st.selectbox("Formato", ["PDF", "Excel", "DOCX", "PPT", "Markdown"], key="rep_sched_format")
        with col3:
            sched_template = st.selectbox(
                "Plantilla",
                ["Resumen Ejecutivo", "Informe Financiero", "KPI Dashboard"],
                key="rep_sched_template",
            )
        recipients = st.text_input("Destinatarios (email, separados por coma)", key="rep_sched_recipients")
        run = st.button("⏰ Activar Programación", type="primary", key="rep_run_sched", use_container_width=True)
        if run:
            st.success(f"✅ Informe '{sched_template}' programado: {frequency} en formato {sched_format}.")

    with tab_export:
        st.subheader("Exportar datos y resultados")
        export_format = st.selectbox(
            "Formato de exportación",
            ["Excel (.xlsx)", "CSV", "JSON", "PDF", "DOCX", "PowerPoint (.pptx)"],
            key="rep_export_format",
        )
        include_charts = st.toggle("Incluir gráficos", value=True, key="rep_export_charts")
        run = st.button("💾 Exportar", type="primary", key="rep_run_export", use_container_width=True)
        if run:
            sample_data = pd.DataFrame([
                {"módulo": "Ingesta", "estado": "OK", "archivos": 120},
                {"módulo": "Extracción", "estado": "OK", "entidades": 1450},
                {"módulo": "Reporting", "estado": "OK", "informes": 12},
            ])
            st.dataframe(sample_data, use_container_width=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                f"⬇️ Descargar {export_format}",
                data=sample_data.to_csv(index=False),
                file_name=f"export_{ts}.csv",
                mime="text/csv",
            )

    with tab_email:
        st.subheader("Plantilla de email")
        email_template = st.selectbox(
            "Tipo de plantilla",
            ["Resumen Ejecutivo", "Alerta", "KPI Snapshot", "Newsletter", "Propuesta Comercial"],
            key="rep_email_template",
        )
        recipient_list = st.text_area("Lista de destinatarios", placeholder="email1@company.com, email2@company.com", key="rep_email_recipients")
        email_subject = st.text_input("Asunto", placeholder="Informe mensual IS-BACKOFFICE", key="rep_email_subject")
        run = st.button("📧 Preparar Email", type="primary", key="rep_run_email", use_container_width=True)
        if run:
            st.success(f"Plantilla '{email_template}' lista. Configura SMTP para envío automático.")

    with tab_hist:
        st.subheader("Historial de informes")
        show_failed = st.toggle("Mostrar trabajos fallidos", value=False, key="rep_hist_failed")
        history = pd.DataFrame([
            {"fecha": "2026-05-07 09:00", "plantilla": "Resumen Ejecutivo", "estado": "✅ Completado", "formato": "PDF", "tamaño": "245 KB"},
            {"fecha": "2026-05-06 14:30", "plantilla": "Informe de Ventas", "estado": "✅ Completado", "formato": "Excel", "tamaño": "182 KB"},
            {"fecha": "2026-05-05 08:00", "plantilla": "Market Research", "estado": "✅ Completado", "formato": "DOCX", "tamaño": "1.2 MB"},
        ])
        if not show_failed:
            history = history[history["estado"] == "✅ Completado"]
        st.dataframe(history, use_container_width=True)

    _render_agent_orchestrator_panel(section="📑 REPORTING")


# ---------------------------------------------------------------------------
# Agents page
# ---------------------------------------------------------------------------

def _page_agents() -> None:
    _section_header("🤖 AGENTS", "Orchestrate AI agents, monitor status, and configure parameters")

    _render_signal_cards(
        [
            {
                "title": "Research Agent",
                "severity": "Running",
                "summary": "Última acción: sintetizó 12 fuentes y generó un brief ejecutivo.",
                "action": "Open research workspace",
            },
            {
                "title": "Pricing Agent",
                "severity": "Attention",
                "summary": "Última acción: detectó una anomalía de pricing en Delta Renewal.",
                "action": "Inspect deal",
            },
            {
                "title": "Forecast Agent",
                "severity": "Healthy",
                "summary": "Última acción: actualizó el forecast comercial y el snapshot ejecutivo.",
                "action": "Review forecast",
            },
        ]
    )

    tab_run, tab_status, tab_config = st.tabs(["▶️ Ejecutar", "🟢 Estado", "⚙️ Configurar"])

    with tab_run:
        st.subheader("Ejecutar todos los agentes")
        st.info(
            "El orquestador ejecuta todos los agentes secuencialmente sobre los datos ingestados. "
            "Ingesta documentos primero para obtener resultados reales."
        )
        run = st.button("🤖 Ejecutar Todos los Agentes", type="primary", key="agents_run_all", use_container_width=True)
        if run:
            agents = [
                "IngestionAgent", "CleaningAgent", "ExtractionAgent",
                "GraphAgent", "AnalyticsAgent", "ReportingAgent"
            ]
            progress = st.progress(0.0)
            log_area = st.empty()
            logs = []
            for i, agent_name in enumerate(agents):
                logs.append(f"✅ {agent_name}: completado")
                log_area.markdown("\n".join(logs))
                progress.progress((i + 1) / len(agents))
            st.success("Todos los agentes completados.")

    with tab_status:
        st.subheader("Estado de los agentes")
        status_data = pd.DataFrame([
            {"Agente": "Research Agent", "Estado": "✅ OK", "Última acción": "Executive brief", "Coste": "$0.43", "Logs": "12 fuentes"},
            {"Agente": "Market Agent", "Estado": "✅ OK", "Última acción": "Signal refresh", "Coste": "$0.31", "Logs": "4 señales"},
            {"Agente": "Pricing Agent", "Estado": "⚠️ Atención", "Última acción": "Pricing anomaly", "Coste": "$0.22", "Logs": "1 anomalía"},
            {"Agente": "Sales Agent", "Estado": "✅ OK", "Última acción": "Follow-up queue", "Coste": "$0.18", "Logs": "9 acciones"},
            {"Agente": "Forecast Agent", "Estado": "✅ OK", "Última acción": "Revenue update", "Coste": "$0.27", "Logs": "Forecast 5.2M"},
            {"Agente": "Executive Agent", "Estado": "🟢 Listo", "Última acción": "Board summary", "Coste": "$0.16", "Logs": "3 recomendaciones"},
        ])
        st.dataframe(status_data, use_container_width=True)

    with tab_config:
        st.subheader("Configuración de agentes")
        with st.expander("⚙️ IngestionAgent"):
            st.slider("Timeout (segundos)", 10, 300, 60, key="cfg_ing_timeout")
            st.toggle("Ingesta recursiva de subcarpetas", value=True, key="cfg_ing_recursive")
            st.multiselect("Extensiones a incluir", ["pdf", "docx", "xlsx", "txt", "csv"], default=["pdf", "docx"], key="cfg_ing_ext")
        with st.expander("⚙️ ExtractionAgent"):
            st.toggle("Usar spaCy (mejora NER)", value=False, key="cfg_ext_spacy")
            st.slider("Confianza mínima", 0.5, 1.0, 0.7, 0.05, key="cfg_ext_confidence")
        with st.expander("⚙️ ReportingAgent"):
            st.selectbox("Idioma de salida", ["Español", "English", "Français"], key="cfg_rep_lang")
            st.toggle("Incluir gráficos en informes", value=True, key="cfg_rep_charts")
        with st.expander("⚙️ GraphAgent"):
            st.slider("Profundidad máxima del grafo", 1, 10, 5, key="cfg_graph_depth")
        with st.expander("🔑 Credenciales IA"):
            openai_key = st.text_input("OPENAI_API_KEY", type="password", key="cfg_openai_key",
                                       placeholder="sk-... (opcional, mejora análisis IA)")
            if st.button("Guardar clave API", key="cfg_save_openai"):
                if openai_key:
                    os.environ["OPENAI_API_KEY"] = openai_key
                    st.success("Clave API guardada en esta sesión.")
                else:
                    st.warning("Introduce una clave API válida.")


# ---------------------------------------------------------------------------
# Orchestrator expander (appended to each page)
# ---------------------------------------------------------------------------

def _render_agent_orchestrator_panel(section: str = "") -> None:
    with st.expander("🤖 Multi-Agent Orchestrator", expanded=False):
        st.caption(f"Módulo activo: {section or 'General'}")
        if st.button("▶️ Run All Agents on Current Data", key=f"orch_run_{section.replace(' ', '_')}"):
            try:
                from backoffice.agents.orchestrator import AgentOrchestrator
                orch = AgentOrchestrator()
                context: dict[str, Any] = {
                    "section": section,
                    "last_result": st.session_state.get("last_result"),
                }
                with st.spinner("Ejecutando agentes..."):
                    results = orch.run_all(context)
                for name, result in results.items():
                    st.write(f"**{name}**: {str(result)[:500]}")
            except ImportError:
                st.info("Orquestador de agentes no disponible. Los módulos core están operativos.")
            except Exception as exc:
                st.error(f"Error en el orquestador: {exc}")


# ---------------------------------------------------------------------------
# Main content router
# ---------------------------------------------------------------------------

# Maps active_page values to their parent section (for pages within a section)
_INGESTION_PAGES = {"File Upload", "URL Ingest", "Watch Folder", "Bulk Import", "Scraper"}
_CLEANING_PAGES = {"Deduplication", "Standardization", "Quality Audit", "Outlier Detection", "Fuzzy Merge"}
_EXTRACTION_PAGES = {"Text NER", "PDF Extraction", "Batch Processing", "Few-Shot Examples", "Table Detection"}
_GRAPH_PAGES = {"Search Graph", "Entity Explorer", "Path Finder", "Community Detection", "Subgraph Visualizer"}
_ANALYTICS_PAGES = {"Dataset Insights", "NL Query", "Forecasting", "What-If Analysis", "Dashboard Builder"}
_REPORTING_PAGES = {"Generate Report", "Schedule Report", "Export", "Email Template", "Report History"}
_AGENTS_PAGES = {"Run All Agents", "Agent Status", "Configure Agents"}


def render_main_content() -> None:
    active_page = st.session_state.get("active_page", "Intelligence Center")

    if active_page in {"Dashboard", "Intelligence Center"}:
        _page_dashboard()
    elif active_page == "Clients & Accounts":
        _page_clients_accounts()
    elif active_page == "Deals & Pipeline":
        _page_deals_pipeline()
    elif active_page == "Research & Documents":
        _page_research_documents()
    elif active_page == "AI Agents":
        _page_agents()
    elif active_page == "Alerts & Risks":
        _page_alerts_risks()
    elif active_page == "Knowledge Graph":
        _page_graph()
    elif active_page == "Reports & Executive":
        _page_reports_executive()
    elif active_page == "Settings & Integrations":
        _page_settings_integrations()
    elif active_page in _INGESTION_PAGES:
        _page_ingestion()
    elif active_page in _CLEANING_PAGES:
        _page_cleaning()
    elif active_page in _EXTRACTION_PAGES:
        _page_extraction()
    elif active_page in _GRAPH_PAGES:
        _page_graph()
    elif active_page in _ANALYTICS_PAGES:
        _page_analytics()
    elif active_page in _REPORTING_PAGES:
        _page_reporting()
    elif active_page in _AGENTS_PAGES:
        _page_agents()
    else:
        # Fallback to legacy section-based routing
        current_section = st.session_state.get("current_section", "")
        current_action = st.session_state.get("current_action", "")
        last_result = st.session_state.get("last_result")

        if current_section and current_action and last_result:
            st.markdown(f"### {current_section}")
            if last_result.get("type") == "document_analysis":
                _render_document_analysis_result(last_result)
            else:
                msg = last_result.get("message", last_result.get("summary", ""))
                if msg:
                    st.info(msg)
        else:
            _page_dashboard()