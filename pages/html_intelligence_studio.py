from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from backoffice.his import HtmlIntelligenceStudio

def _split_paths(text: str) -> list[str]:
    parts: list[str] = []
    for raw in (text or "").splitlines():
        cleaned = raw.strip().strip('"').strip("'")
        if cleaned:
            parts.append(cleaned)
    return parts


def _render_inline_preview(studio: HtmlIntelligenceStudio, html_path: str, key: str = "his_preview") -> None:
    try:
        content = studio.build_inline_preview_html(html_path)
    except Exception as exc:
        st.error(str(exc))
        return
    components.html(content, height=900, scrolling=True)


def _render_html_portability_guard(studio: HtmlIntelligenceStudio) -> None:
    current_html = st.session_state.get("his_current_html", "")
    if not current_html:
        st.info("No HTML generated yet. The portability guard will validate the generated file once available.")
        return

    guard_enabled = st.session_state.get("his_portability_guard_enabled", True)
    if not guard_enabled:
        st.warning("Portability guard disabled. HTMLs may still depend on local assets.")
        return

    try:
        result = studio.validate_html_stability(current_html)
        if result["portable"]:
            st.success("HTML portable y estable: sin rutas de assets locales visibles en el fichero final.")
        else:
            st.warning("HTML no estable fuera del PC: se detectan referencias locales. Se recomienda aplicar la garantía de autocontenido.")
            fixed = studio.guarantee_standalone_html(current_html)
            if fixed["portable"]:
                st.success("Garantía aplicada: el HTML ha sido convertido a formato autocontenido y estable.")
                st.session_state["his_current_html"] = current_html
            else:
                st.error(f"La garantía no pudo corregir todas las referencias: {fixed['local_asset_references']}")
        st.json(result)
    except Exception as exc:
        st.error(str(exc))


def _sidebar_editor(studio: HtmlIntelligenceStudio) -> None:
    st.sidebar.markdown("## HIS Visual Editor")
    html_path = st.session_state.get("his_current_html")
    model_path = st.session_state.get("his_current_model")
    if not html_path:
        st.sidebar.info("Generate or run a mission first to enable editor controls.")
        return

    st.sidebar.caption("Workspace overlay mode. Corporate visual style is locked and cannot be modified from editor tools.")

    if model_path:
        st.sidebar.markdown("### Structural AI Command")
        dom_command = st.sidebar.text_area(
            "DOM command",
            value="Crear capítulo y añadir KPI",
            key="his_dom_command",
            height=100,
        )
        if st.sidebar.button("Apply DOM Command", use_container_width=True):
            try:
                result = studio.run_ai_command(model_path, dom_command)
                st.session_state["his_last_mission"] = result
                st.session_state["his_current_html"] = result.get("html_path", "")
                st.session_state["his_current_model"] = result.get("document_model_path", model_path)
                st.sidebar.success("DOM command applied")
            except Exception as exc:
                st.sidebar.error(str(exc))
    else:
        st.sidebar.info("DOM model path not available yet. Generate document first.")

    st.sidebar.markdown("### Insert Image")
    image_path = st.sidebar.text_input("Image path", key="his_insert_image_path")
    heading = st.sidebar.text_input("Heading", value="TAILORED AUTOMATION", key="his_insert_heading")
    if st.sidebar.button("Insert image under heading", use_container_width=True):
        try:
            if not model_path:
                raise RuntimeError("Document model path is required for DOM-only image insertion.")
            mission = studio.insert_image_under_heading(
                document_model_path=model_path,
                image_path=image_path,
                heading_text=heading,
                section_path=["Home", "Chapter 1", heading],
                author="Assistant",
            )
            st.session_state["his_last_mission"] = mission
            st.session_state["his_current_html"] = mission["html_path"]
            st.session_state["his_current_model"] = mission.get("document_model_path", model_path)
            st.sidebar.success("Image inserted and new version generated")
            st.session_state["his_refresh_preview"] = True
        except Exception as exc:
            st.sidebar.error(str(exc))


def main() -> None:
    st.set_page_config(page_title="HTML Intelligence Studio", page_icon="🧠", layout="wide")

    try:
        from backoffice.theme import inject_theme

        inject_theme()
    except Exception:
        pass

    studio = HtmlIntelligenceStudio()

    if "his_editor_mode" not in st.session_state:
        st.session_state["his_editor_mode"] = True

    if st.session_state.get("his_editor_mode"):
        _sidebar_editor(studio)

    st.title("🧠 HTML Intelligence Studio (HIS)")
    st.caption("Industrial HTML Generation & AI Editing Platform")

    tab_dashboard, tab_explorer, tab_generate, tab_corporate, tab_preview, tab_editor, tab_ai, tab_assets, tab_versions, tab_missions, tab_quality, tab_knowledge, tab_publication, tab_config = st.tabs(
        [
            "Dashboard",
            "Document Explorer",
            "Generation Panel",
            "Corporate Publishing",
            "Preview",
            "Editor",
            "AI Command Layer",
            "Assets",
            "Versions",
            "Mission History",
            "Quality Dashboard",
            "Knowledge Panel",
            "Publication",
            "Configuración",
        ]
    )

    with tab_dashboard:
        docs = studio.list_documents()
        history = studio.read_mission_history(500)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Documents", len(docs))
        c2.metric("Missions", len(history))
        c3.metric("Published", sum(1 for d in docs if d.get("status") == "Published"))
        c4.metric("Editing", sum(1 for d in docs if d.get("status") == "Editing"))
        st.caption("RC1 consolidated mode: only HIS V3 pipeline is active.")

    with tab_explorer:
        st.subheader("Document Explorer")
        docs = studio.list_documents()
        if not docs:
            st.info("No documents found yet.")
        else:
            st.dataframe(
                [
                    {
                        "Nombre": d.get("name", ""),
                        "Cliente": d.get("client", ""),
                        "Proyecto": d.get("project", ""),
                        "Categoría": d.get("category", ""),
                        "Idioma": d.get("language", ""),
                        "Versión": d.get("version", 0),
                        "Estado": d.get("status", "Draft"),
                        "Executive Score": d.get("executive_score", 0.0),
                        "Fecha": d.get("date", ""),
                        "Última edición": d.get("last_edit", ""),
                        "Model Path": d.get("document_model_path", ""),
                    }
                    for d in docs
                ],
                use_container_width=True,
                hide_index=True,
            )
            selected = st.selectbox("Abrir documento", options=["—"] + [d.get("document_model_path", "") for d in docs])
            if selected != "—" and st.button("Abrir en Editor", type="primary"):
                st.session_state["his_current_model"] = selected
                model_data = studio.read_json(selected, {})
                last_html = ""
                try:
                    versions = model_data.get("version_history", [])
                    if versions:
                        last_html = versions[-1].get("output_files", {}).get("html", "")
                except Exception:
                    pass
                st.session_state["his_current_html"] = last_html
                st.success("Documento cargado en workspace.")

    with tab_generate:
        with st.form("his_generate_form"):
            format_catalog = studio.get_format_catalog()
            format_options = [item["label"] for item in format_catalog["formats"]]

            st.markdown("### Inputs del informe")
            c1, c2, c3 = st.columns(3)
            with c1:
                selected_format_label = st.selectbox("Formato que se desea", format_options, index=0)
                selected_format = next((item for item in format_catalog["formats"] if item["label"] == selected_format_label), format_catalog["formats"][0])
                document_name = st.text_input("Nombre del documento", value=f"{selected_format['label']} Report")
                project = st.text_input("Proyecto", value="Industrial_Intelligence")
                client = st.text_input("Cliente al que va dirigido", value="INGECART")
                category = st.text_input("Categoría", value="executive")
            with c2:
                language = st.selectbox("Idioma", ["English", "Español", "Bilingual"], index=2)
                theme_profile = st.selectbox(
                    "Theme",
                    ["ingecart_industrial", "service_engine"],
                    index=0,
                    help="El formato Ingecart usa la identidad industrial corporativa.",
                )
                source_format = st.selectbox(
                    "Formato origen",
                    ["Auto", "PowerPoint", "Word", "PDF", "Markdown", "HTML", "Folder", "Images", "Text", "Mixed"],
                    index=0,
                )
                source_path = st.text_input("Documento origen (ruta)", value="")
                output_root = st.text_input("Ruta de salida", value="")
            with c3:
                audience = st.text_input("Público objetivo", value="Executive Board")
                objective = st.text_area("Objetivo del documento", value="Generar un informe ejecutivo con estructura técnica y narrativa industrial clara.", height=90)
                comments = st.text_area("Comentarios de edición", value="", height=90)

            st.markdown("#### Contexto del caso")
            case_context = st.text_area(
                "Contexto del cliente y escenario industrial",
                value=(
                    "Elegir la referencia técnica correcta, mantener flujo estable, reducir WIP, automatizar logística y preparar la planta para crecimiento futuro. "
                    "En este caso centrado en PAIGE / Ingecart, la diferencia real la marca la continuidad del flujo y la trazabilidad del material."
                ),
                height=140,
            )

            st.markdown("#### Borrador / instrucciones / ubicaciones de imágenes y URLs")
            draft_text = st.text_area(
                "Borrador editable del informe",
                value=(
                    "Se recomienda abrir con una tesis clara: el valor real no está en la máquina aislada sino en la capacidad del sistema para sostener flujo, trazabilidad y producción útil. "
                    "La salida de línea, el WIP, la logística automatizada y la gestión del residuo forman un circuito que debe evaluarse como un sistema integrado."
                ),
                height=120,
            )
            image_url_notes = st.text_area(
                "Indicaciones para imágenes o URLs",
                value="Insertar imagen de layout o proceso en el bloque de contexto. Añadir URL de benchmark o referencia industrial en la sección de evidencias. Ubicar imagen de flujo y de AMR/RFID en el capítulo diferencial.",
                height=90,
            )

            st.markdown("#### Fuentes de entrada: contenido, contexto y análisis")
            multi_paths_text = st.text_area("Rutas relevantes (una por línea)", value="\n".join(selected_format.get("source_bundle", [])), height=110)
            uploaded_files = st.file_uploader(
                "Carga de archivos para contenido, contexto y análisis",
                type=["pptx", "ppt", "docx", "pdf", "md", "txt", "html", "htm", "jpg", "jpeg", "png"],
                accept_multiple_files=True,
            )

            st.markdown("### Catálogo de formatos disponibles")
            st.caption(f"Formato activo: {selected_format['label']} · plantilla de referencia: {selected_format.get('template_reference') or 'No disponible aún'}")
            st.json({
                "formato": selected_format["label"],
                "descripcion": selected_format["description"],
                "capabilities": format_catalog["intelligence_capabilities"],
                "mission_policy": format_catalog["mission_policy"],
                "workbench_paths": format_catalog["workbench_paths"],
            })

            instruction_text = st.text_area(
                "Instrucciones finales para la generación",
                value=(
                    f"Formato requerido: {selected_format['label']}. "
                    f"Cliente: {client}. "
                    f"Contexto: {case_context}. "
                    f"Objetivo: {objective}. "
                    f"Requisitos: usar la arquitectura documental del formato Ingecart como base, mantener narrativa ejecutiva, añadir trazabilidad, flujo, WIP, logística, desperdicio, escalabilidad, y señalar dónde deben ir las imágenes o URLs. "
                    f"Borrador: {draft_text}. "
                    f"Notas de imagen/URL: {image_url_notes}."
                ),
                height=140,
            )

            submitted = st.form_submit_button("Generate HTML", type="primary")

        if submitted:
            uploaded_paths = studio.save_uploaded_sources(uploaded_files)
            all_sources = []
            if source_path.strip():
                all_sources.append(source_path.strip())
            all_sources.extend(_split_paths(multi_paths_text))
            all_sources.extend(uploaded_paths)

            with st.status("Mission Manager: analyzing and generating HTML...", expanded=True):
                result = studio.create_document(
                    document_name=document_name,
                    project=project,
                    client=client,
                    category=category,
                    language=language,
                    source_format=source_format,
                    sources=all_sources,
                    output_root=output_root or None,
                    comments=comments,
                    objective=objective,
                    audience=audience,
                    instruction_text=instruction_text,
                    theme_profile=theme_profile,
                )

            st.session_state["his_last_result"] = result
            st.session_state["his_current_html"] = result.get("html_path", "")
            st.session_state["his_current_model"] = result.get("document_model_path", "")
            st.session_state["his_last_context"] = {
                "formato": selected_format_label,
                "cliente": client,
                "contexto": case_context,
                "borrador": draft_text,
                "imagenes_urls": image_url_notes,
            }
            st.success("HTML generated successfully")
            st.json(result)
            if result.get("html_path"):
                st.markdown("### Internal Preview")
                _render_inline_preview(studio, result["html_path"], key="his_preview_generated")

    with tab_corporate:
        st.subheader("Corporate Publishing")
        st.caption("Generate governed EN/ES derivatives from authorized repositories.")
        with st.form("his_corporate_publish_form"):
            c1, c2 = st.columns(2)
            with c1:
                corporate_repository = st.selectbox(
                    "Source repository",
                    ["ai_factory", "adaptive_sales_engine", "ingesite"],
                )
                corporate_relative_path = st.text_input(
                    "Relative source path",
                    value="PCG_MIDDLETOWN_CONVERTING_AUDIT_2026-08-17.html",
                )
                corporate_title = st.text_input("Document title", value="Corporate Intelligence Report")
            with c2:
                corporate_client = st.text_input("Delivery client", value="INGECART")
                corporate_project = st.text_input("Project", value="Corporate Publishing")
                corporate_profile = st.selectbox("Delivery profile", ["standard", "cascades_pdf_only"])
                corporate_languages = st.multiselect("Languages", ["en", "es"], default=["en", "es"])
                default_formats = ["pdf"] if corporate_profile == "cascades_pdf_only" else ["html", "pdf", "docx"]
                corporate_formats = st.multiselect(
                    "Formats",
                    ["html", "pdf", "docx", "xlsx", "pptx"],
                    default=default_formats,
                    disabled=corporate_profile == "cascades_pdf_only",
                )
            corporate_submitted = st.form_submit_button("Generate corporate document", type="primary")
        if corporate_submitted:
            try:
                formats = ["pdf"] if corporate_profile == "cascades_pdf_only" else corporate_formats
                corporate_result = studio.publish_corporate_html(
                    repository_id=corporate_repository,
                    relative_path=corporate_relative_path,
                    title=corporate_title,
                    client=corporate_client,
                    project=corporate_project,
                    formats=formats,
                    languages=corporate_languages,
                    profile_id=corporate_profile,
                )
                st.session_state["his_last_corporate_document"] = corporate_result
                st.success(f"Corporate document {corporate_result['document_id']} is {corporate_result['status']}.")
                st.json(corporate_result)
            except Exception as exc:
                st.error(str(exc))

        corporate_documents = studio.list_corporate_documents()
        if corporate_documents:
            st.markdown("### Corporate Registry")
            st.dataframe(
                [
                    {
                        "ID": item.get("document_id"),
                        "Title": item.get("title"),
                        "Client": item.get("client"),
                        "Version": item.get("version"),
                        "Languages": ", ".join(item.get("languages", [])),
                        "Status": item.get("status"),
                        "Profile": item.get("delivery_policy", {}).get("profile_id"),
                    }
                    for item in corporate_documents
                ],
                use_container_width=True,
                hide_index=True,
            )
            selected_corporate_id = st.selectbox(
                "Document to package",
                [item.get("document_id", "") for item in corporate_documents],
            )
            if st.button("Create governed delivery package"):
                try:
                    package_path = studio.package_corporate_document(selected_corporate_id)
                    st.success(f"Package created: {package_path}")
                except Exception as exc:
                    st.error(str(exc))

    with tab_preview:
        st.subheader("Preview")
        current_html = st.session_state.get("his_current_html", "")
        if current_html:
            _render_inline_preview(studio, current_html, key="his_preview_main")
        else:
            st.info("No HTML loaded yet.")

    with tab_editor:
        st.subheader("Editor Workspace")
        st.caption("Editor manipulates DOM through mission commands. Theme and rendering are immutable from overlay controls.")
        current_html = st.session_state.get("his_current_html", "")
        current_model = st.session_state.get("his_current_model", "")
        st.write("Model:", current_model or "—")
        st.write("HTML:", current_html or "—")
        if current_html:
            _render_inline_preview(studio, current_html, key="his_preview_editor")

    with tab_ai:
        st.subheader("AI Command Layer")
        base_result = st.session_state.get("his_last_result", {})
        model_path_default = base_result.get("document_model_path", "")
        model_path = st.text_input("Document model path", value=model_path_default)
        command = st.text_area(
            "Mission command",
            value="Haz el texto más ejecutivo y añade gráficos",
            height=120,
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Run AI Mission Command", type="primary", use_container_width=True):
                try:
                    with st.status("Executing AI mission command...", expanded=True):
                        mission_result = studio.run_ai_command(model_path, command)
                    st.session_state["his_last_mission"] = mission_result
                    st.session_state["his_current_html"] = mission_result.get("html_path", "")
                    st.session_state["his_current_model"] = mission_result.get("document_model_path", model_path)
                    st.success("Mission completed")
                    st.json(mission_result)
                    if mission_result.get("html_path"):
                        _render_inline_preview(studio, mission_result["html_path"], key="his_preview_mission")
                except Exception as exc:
                    st.error(str(exc))

        with c2:
            if st.button("Run First Mission (TAILORED AUTOMATION)", use_container_width=True):
                try:
                    with st.status("Running first mandatory mission...", expanded=True):
                        mission_result = studio.run_first_mission()
                    st.session_state["his_last_mission"] = mission_result
                    st.session_state["his_current_html"] = mission_result.get("html_path", "")
                    st.session_state["his_current_model"] = mission_result.get("document_model_path", "")
                    st.success("First mission executed")
                    st.json(mission_result)
                    if mission_result.get("html_path"):
                        _render_inline_preview(studio, mission_result["html_path"], key="his_preview_first_mission")
                except Exception as exc:
                    st.error(str(exc))

    with tab_assets:
        st.subheader("Assets")
        result = st.session_state.get("his_last_result", {})
        asset_registry_path = result.get("asset_registry_path", "")
        if asset_registry_path:
            asset_registry = studio.read_json(asset_registry_path, {})
            st.write("Asset root:", asset_registry.get("asset_root", ""))
            st.dataframe(asset_registry.get("items", []), use_container_width=True, hide_index=True)
        else:
            st.info("Generate a document to populate the asset registry.")

    with tab_versions:
        st.subheader("Version Manager")
        mission = st.session_state.get("his_last_mission")
        result = st.session_state.get("his_last_result")
        if result:
            st.markdown("### Latest Generation")
            st.json(result)
            if result.get("publication_state"):
                st.markdown(f"**Publication State:** {result.get('publication_state')}")
            if result.get("evidence_zip_path"):
                st.markdown(f"**Evidence ZIP:** {result.get('evidence_zip_path')}")
        if mission:
            st.markdown("### Latest Mission")
            st.json(mission)
        if not result and not mission:
            st.info("No version data available yet.")

    with tab_missions:
        st.subheader("Mission History")
        rows = studio.read_mission_history(500)
        if not rows:
            st.info("No missions registered yet.")
        else:
            st.dataframe(rows, use_container_width=True, hide_index=True)

    with tab_quality:
        st.subheader("Quality Dashboard")
        result = st.session_state.get("his_last_result", {})
        qpath = result.get("quality_report_path", "")
        if qpath:
            quality = studio.read_json(qpath, {})
            selected_scores = quality.get("selected_scores", {})
            selected_quality = quality.get("selected_quality", {})
            metrics = selected_quality.get("metrics", {})
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Executive Quality", selected_scores.get("executive_quality_score", 0.0))
            c2.metric("Theme", metrics.get("theme_compliance", 0.0))
            c3.metric("Accessibility", metrics.get("accessibility", 0.0))
            c4.metric("Responsive", metrics.get("responsive", 0.0))
            st.json(quality)
        else:
            st.info("Run a generation mission to get quality metrics.")

    with tab_knowledge:
        st.subheader("Knowledge Panel")
        result = st.session_state.get("his_last_result", {})
        kpath = result.get("knowledge_package_path", "")
        mpath = result.get("enterprise_memory_path", "")
        tpath = result.get("truth_graph_path", "")
        if kpath:
            st.markdown("### Knowledge Package")
            st.json(studio.read_json(kpath, {}))
        if mpath:
            st.markdown("### Enterprise Memory")
            st.json(studio.read_json(mpath, {}))
        if tpath:
            st.markdown("### Truth Graph")
            st.json(studio.read_json(tpath, {}))
        if not kpath:
            st.info("No knowledge artifacts yet.")

    with tab_publication:
        st.subheader("Publication")
        model_path = st.session_state.get("his_current_model") or st.session_state.get("his_last_result", {}).get("document_model_path", "")
        st.write("Model path:", model_path or "—")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Publish", type="primary", use_container_width=True):
                try:
                    out = studio.publish_document(model_path)
                    st.success(f"Published at {out.get('published_at','')}")
                    st.json(out)
                except Exception as exc:
                    st.error(str(exc))
        with c2:
            if st.button("Export ZIP (Published only)", use_container_width=True):
                try:
                    zip_path = studio.export_release_bundle(model_path)
                    st.success(f"ZIP created: {zip_path}")
                except Exception as exc:
                    st.error(str(exc))

    with tab_config:
        st.subheader("Configuración")
        st.write("Corporate theme source:", str(studio.corporate_model_path))

        st.markdown("### HTML portability guardrail")
        st.caption("Bloque de garantía para que cada HTML generado sea estable fuera del PC del autor: sin enlaces locales a CSS, JS ni imágenes si no van embebidos.")
        st.session_state["his_portability_guard_enabled"] = st.checkbox(
            "Activar garantía de HTML portátil/autocontenido",
            value=st.session_state.get("his_portability_guard_enabled", True),
            help="Cuando está activo, el motor valida y, si es necesario, convierte referencias locales en contenido embebido (base64/data URI).",
        )
        if st.button("Validar HTML actual", type="secondary"):
            _render_html_portability_guard(studio)

        st.markdown("### Repository Catalog")
        catalog = studio.get_repository_catalog()
        st.json(catalog)
        st.markdown("### Theme Profiles")
        st.json(studio.theme_profiles())
        with st.expander("Asset discovery sample", expanded=False):
            candidates = studio.resolve_asset_candidates(limit=30)
            st.write(f"Candidates discovered: {len(candidates)}")
            st.dataframe([{"path": p} for p in candidates], use_container_width=True, hide_index=True)

        st.markdown("### AHDE Operational Certification")
        c1, c2 = st.columns(2)
        max_iterations = c1.number_input("Max repair iterations", min_value=1, max_value=12, value=5, step=1)
        max_minutes = c2.number_input("Max execution time (minutes)", min_value=5, max_value=120, value=30, step=5)
        if st.button("Run Operational Certification", type="primary"):
            with st.status("Executing AHDE certification and recovery loops...", expanded=True):
                report = studio.run_operational_certification(
                    max_iterations=int(max_iterations),
                    max_minutes=int(max_minutes),
                )
            st.session_state["his_operational_certification"] = report
            st.success(report.get("mission_status", "Completed"))
            st.json(report)

        if st.session_state.get("his_operational_certification"):
            st.markdown("### Last Certification")
            st.json(st.session_state["his_operational_certification"])
        st.caption("RC1 policy: direct HTML editing is disabled for mission operations; use DOM commands only.")
        st.caption("Official engine: HTML Intelligence Studio V3")


if __name__ == "__main__":
    main()
