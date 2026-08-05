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

    tab_dashboard, tab_explorer, tab_generate, tab_preview, tab_editor, tab_ai, tab_assets, tab_versions, tab_missions, tab_quality, tab_knowledge, tab_publication, tab_config = st.tabs(
        [
            "Dashboard",
            "Document Explorer",
            "Generation Panel",
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
            c1, c2, c3 = st.columns(3)
            with c1:
                document_name = st.text_input("Nombre del documento", value="HIS Corporate Document")
                project = st.text_input("Proyecto", value="Corrugated_Plant_Automation")
                client = st.text_input("Cliente", value="INGECART")
                category = st.text_input("Categoría", value="pie")
            with c2:
                language = st.selectbox("Idioma", ["English", "Español", "Bilingual"], index=2)
                source_format = st.selectbox(
                    "Formato origen",
                    ["Auto", "PowerPoint", "Word", "PDF", "Markdown", "HTML", "Folder", "Images", "Text", "Mixed"],
                    index=0,
                )
                source_path = st.text_input("Documento origen (ruta)", value="")
                output_root = st.text_input("Ruta de salida", value="")
            with c3:
                comments = st.text_area("Comentarios", value="", height=90)
                objective = st.text_area("Objetivo del documento", value="Generate an Executive Report", height=90)
                audience = st.text_input("Público objetivo", value="Executive Board")

            st.markdown("#### Fuentes de entrada")
            multi_paths_text = st.text_area("Varias rutas (una por línea)", value="", height=110)
            uploaded_files = st.file_uploader(
                "Drag & Drop / Upload",
                type=["pptx", "ppt", "docx", "pdf", "md", "txt", "html", "htm", "jpg", "jpeg", "png"],
                accept_multiple_files=True,
            )
            instruction_text = st.text_area(
                "Caja de texto (instrucciones)",
                value="Genera un Executive Report",
                height=120,
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
                )

            st.session_state["his_last_result"] = result
            st.session_state["his_current_html"] = result.get("html_path", "")
            st.session_state["his_current_model"] = result.get("document_model_path", "")
            st.success("HTML generated successfully")
            st.json(result)
            if result.get("html_path"):
                st.markdown("### Internal Preview")
                _render_inline_preview(studio, result["html_path"], key="his_preview_generated")

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
        st.caption("RC1 policy: direct HTML editing is disabled for mission operations; use DOM commands only.")
        st.caption("Official engine: HTML Intelligence Studio V3")


if __name__ == "__main__":
    main()
