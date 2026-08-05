from __future__ import annotations

from pathlib import Path

import streamlit as st

from backoffice.pie import PresentationIntelligenceMissionManager


def _default_source() -> str:
    return r"C:\Users\Inaki Senar\Documents\INGECART\MARKETING\CONTENT\Corrugated Plant Automation Solutions v2.pptx"


def main() -> None:
    st.set_page_config(page_title="Presentation Intelligence Engine", page_icon="🧠", layout="wide")
    st.title("🧠 Presentation Intelligence Engine (PIE)")
    st.caption("Transforma presentaciones corporativas en HTML moderno, responsivo y reutilizable.")

    with st.expander("Mission Policy", expanded=False):
        st.markdown(
            """
- AHDE always enabled: uncertainties are resolved through hypothesis generation and scoring.
- The engine generates two outputs:
  1. Slide Flow HTML (continuous scroll)
  2. Smart HTML Reconstruction (semantic components)
- Deliverables include technical report, differences report, component matrix, theme, assets, and mission evidence.
            """
        )

    source = st.text_input("Source PPTX", value=_default_source())
    output_root = st.text_input("Output root", value="reports/pie")

    run_clicked = st.button("Run PIE Mission", type="primary")
    if not run_clicked:
        return

    if not source.strip():
        st.error("Provide a source PPTX path.")
        return

    source_path = Path(source).expanduser()
    if not source_path.exists():
        st.error(f"Source file not found: {source_path}")
        return

    with st.status("Running PIE mission...", expanded=True) as status:
        st.write("Initializing Mission Manager and agent orchestration...")
        manager = PresentationIntelligenceMissionManager()

        try:
            result = manager.run(str(source_path), output_root)
        except Exception as exc:  # noqa: BLE001
            status.update(label="PIE mission failed", state="error")
            st.exception(exc)
            return

        status.update(label="PIE mission completed", state="complete")

    st.success("PIE mission completed successfully.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Output files")
        st.write("Run ID:", result.run_id)
        st.write("Output directory:", result.output_dir)
        st.write("Version 1 HTML:", result.version_1_html)
        st.write("Version 2 HTML:", result.version_2_html)
        st.write("Corporate CSS:", result.corporate_css)
        st.write("Theme tokens:", result.theme_file)

    with col2:
        st.markdown("### Reports and logs")
        st.write("Technical report:", result.technical_report)
        st.write("Differences report:", result.differences_report)
        st.write("Component matrix:", result.components_matrix)
        st.write("Evidence file:", result.evidence_file)
        st.write("AHDE decisions:", result.decisions_file)
        st.write("Mission log:", result.mission_log_file)

    st.info("Open the generated HTML files in your browser for final review.")


if __name__ == "__main__":
    main()
