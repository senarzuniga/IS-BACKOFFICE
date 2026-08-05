from __future__ import annotations

from pathlib import Path

import streamlit as st

from backoffice.dipc import DocumentIntelligencePublishingCenter

DEFAULT_SOURCE = r"C:\Users\Inaki Senar\Documents\INGECART\MARKETING\CONTENT\Corrugated Plant Automation Solutions v2.pptx"


def main() -> None:
    st.set_page_config(page_title="DIPC", page_icon="📚", layout="wide")
    st.title("📚 Document Intelligence & Publishing Center")
    st.caption("Subsistema corporativo para generación, transformación, publicación, mantenimiento y versionado documental.")

    center = DocumentIntelligencePublishingCenter()

    tab_build, tab_mission = st.tabs(["Build Document", "Run Mission"])

    with tab_build:
        source = st.text_input("Source PPTX", value=DEFAULT_SOURCE, key="dipc_source")
        output_root = st.text_input("Output root", value="reports/dipc", key="dipc_output_root")
        if st.button("Build DIPC Document", type="primary"):
            path = Path(source)
            if not path.exists():
                st.error(f"Source not found: {path}")
            else:
                with st.status("Building DIPC document...", expanded=True):
                    result = center.build_from_powerpoint(str(path), output_root)
                _render_result(result)

    with tab_mission:
        model_path = st.text_input("Document model path", value="", key="dipc_model_path")
        command = st.text_area("Mission command", value="Hazlo más ejecutivo y añade gráficos", key="dipc_command")
        output_root_cmd = st.text_input("Mission output root", value="reports/dipc", key="dipc_output_root_cmd")
        if st.button("Run Mission Command"):
            path = Path(model_path)
            if not path.exists():
                st.error(f"Document model not found: {path}")
            elif not command.strip():
                st.error("Provide a command.")
            else:
                with st.status("Executing DIPC mission...", expanded=True):
                    result = center.apply_mission(str(path), command, output_root_cmd)
                _render_result(result)


def _render_result(result) -> None:
    st.success("DIPC mission completed.")
    col1, col2 = st.columns(2)
    with col1:
        st.write("Run ID:", result.run_id)
        st.write("Output dir:", result.output_dir)
        st.write("Document model:", result.document_model_path)
        st.write("Theme CSS:", result.theme_css_path)
        st.write("Preview manifest:", result.preview_manifest_path)
    with col2:
        st.write("Knowledge package:", result.knowledge_package_path)
        st.write("Enterprise memory:", result.enterprise_memory_path)
        st.write("Mission log:", result.mission_log_path)
    st.markdown("### Publication Outputs")
    for key, value in result.publication_outputs.items():
        st.write(f"{key}: {value}")


if __name__ == "__main__":
    main()
