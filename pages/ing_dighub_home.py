from __future__ import annotations

from pathlib import Path
from typing import Dict

import streamlit as st

from backoffice.ing_dighub_audit import run_self_audit, write_html_report
from backoffice.ui.components.consulting_brand import CONSULTING_HTML_REPORT, CONSULTING_QUICKSTART
from backoffice.ing_dighub_ui_support import (
    build_capability_map,
    coordinator_snapshot,
    knowledge_stats,
    latest_reports,
    module_table,
    open_projects_count,
    pending_reviews_count,
    recent_missions,
)


REPO_ROOT = Path(__file__).resolve().parent.parent


def _jump(page: str) -> None:
    st.switch_page(page)


def _save_uploaded(uploaded_file, target_dir: Path) -> str:
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / uploaded_file.name
    target.write_bytes(uploaded_file.getbuffer())
    return str(target)


def _coordinator_widget(data: Dict[str, object]) -> None:
    st.markdown("### AI Coordinator Status")
    mode = str(data.get("current_mode", "LOCAL EXECUTION MODE"))
    if mode == "LOCAL EXECUTION MODE":
        st.warning("LOCAL EXECUTION MODE")
    else:
        st.success("AI-FACTORY CONNECTED")

    st.write(f"Coordinator Status: {data.get('status', 'unknown')}")
    st.write(f"Current Mode: {mode}")
    st.write(f"Local / AI-FACTORY: {data.get('runtime', 'local')}")
    st.write(f"Approval Status: {data.get('approval_status', 'auto-approval')}")
    st.write(f"Evidence Runtime: {data.get('evidence_runtime', 'enabled')}")
    st.write(f"Knowledge Runtime: {data.get('knowledge_runtime', 'enabled')}")
    st.write(f"Mission Runtime: {data.get('mission_runtime', 'enabled')}")
    st.write(f"Governance Runtime: {data.get('governance_runtime', 'enabled')}")


def main() -> None:
    st.set_page_config(page_title="ING_DIGHUB Home", page_icon="🏭", layout="wide")

    try:
        from backoffice.theme import inject_theme
        inject_theme()
    except Exception:
        pass

    st.markdown(
        """
        <style>
          .ing-card {background:var(--bg-card);border:1px solid var(--border-subtle);border-radius:10px;padding:14px;margin-bottom:8px;}
          .ing-card:hover {border-color:var(--accent);}
          .ing-title {font-size:1rem;font-weight:700;color:var(--text-primary);margin-bottom:6px;}
          .ing-label {font-size:.86rem;color:var(--text-secondary);}
          .ing-hero {background:linear-gradient(120deg,var(--bg-surface),var(--bg-card));border:1px solid var(--border-default);border-left:3px solid var(--accent);color:var(--text-primary);border-radius:12px;padding:18px 24px;margin-bottom:16px;}
          .ing-hero h1 {color:var(--text-primary)!important;margin:0;}
          .ing-hero p {color:var(--text-secondary)!important;margin:4px 0 0;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='ing-hero'><h1>🏭 ING_DIGHUB</h1><p>Industrial Digital Hub Main Workbench</p></div>", unsafe_allow_html=True)

    coord = coordinator_snapshot()
    missions = recent_missions(REPO_ROOT)
    kstats = knowledge_stats(REPO_ROOT)
    reports = latest_reports(REPO_ROOT)

    left, center, right = st.columns([1.1, 2.2, 1.1], gap="large")

    with left:
        st.markdown("<div class='ing-card'><div class='ing-title'>Mission Manager</div></div>", unsafe_allow_html=True)
        if st.button("Open Mission Manager", use_container_width=True):
            _jump("pages/ing_dighub_mission_manager.py")

        st.markdown("<div class='ing-card'><div class='ing-title'>Knowledge Hub</div></div>", unsafe_allow_html=True)
        if st.button("Open Knowledge Hub", use_container_width=True, key="top_open_knowledge_hub"):
            _jump("pages/ing_dighub_knowledge_hub.py")

        st.markdown("<div class='ing-card'><div class='ing-title'>Digital Twin</div></div>", unsafe_allow_html=True)
        if st.button("Open Enterprise Digital Twin", use_container_width=True):
            _jump("pages/ing_dighub_digital_twin.py")

        st.markdown("<div class='ing-card'><div class='ing-title'>Engineering</div></div>", unsafe_allow_html=True)
        if st.button("Open Engineering Workbench", use_container_width=True):
            _jump("pages/industrial_engineering_platform.py")

        st.markdown("<div class='ing-card'><div class='ing-title'>ERP Profesional</div></div>", unsafe_allow_html=True)
        if st.button("Open ERP Profesional Module", use_container_width=True):
            _jump("pages/erp_profesional.py")
        if st.button("Open Partes y Proyectos", use_container_width=True):
            _jump("pages/partes_trabajo.py")
        if st.button("Open Facturacion ERP", use_container_width=True):
            _jump("pages/facturacion.py")
        if st.button("Open CTA R&D Funding Engine", use_container_width=True):
            _jump("pages/rd_funding.py")
        if st.button("Open Funding Consulting Center", use_container_width=True):
            _jump("pages/funding_consulting_center.py")

        st.markdown("<div class='ing-card'><div class='ing-title'>Simulation</div></div>", unsafe_allow_html=True)
        if st.button("Open Plant Simulator", use_container_width=True):
            _jump("pages/plant_simulator.py")

        st.markdown("<div class='ing-card'><div class='ing-title'>Executive Intelligence</div></div>", unsafe_allow_html=True)
        if st.button("Open Competitive Intelligence", use_container_width=True):
            _jump("pages/competitive_intelligence.py")

        st.markdown("<div class='ing-card'><div class='ing-title'>Reports</div></div>", unsafe_allow_html=True)
        if st.button("Open Report Center", use_container_width=True):
            _jump("pages/project_closeout.py")

        st.markdown("<div class='ing-card'><div class='ing-title'>Documents</div></div>", unsafe_allow_html=True)
        if st.button("Open HTML Intelligence Studio", use_container_width=True):
            _jump("pages/html_intelligence_studio.py")

        st.markdown("<div class='ing-card'><div class='ing-title'>💼 Commercial</div></div>", unsafe_allow_html=True)
        if st.button("📄 Service Proposal Engine", use_container_width=True):
            _jump("pages/service_proposal_engine.py")
        if st.button("🧩 SPOE Workbench (legacy)", use_container_width=True):
            _jump("pages/spoe_workbench.py")

        st.markdown("<div class='ing-card'><div class='ing-title'>Administration</div></div>", unsafe_allow_html=True)
        if st.button("Open Administration", use_container_width=True):
            _jump("pages/instruction_panel.py")

        _coordinator_widget(coord)

    with center:
        st.subheader("Executive Dashboard")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Recent Missions", len(missions))
        m2.metric("Knowledge Assets", kstats.get("knowledge_assets", 0))
        m3.metric("Pending Reviews", pending_reviews_count(REPO_ROOT))
        m4.metric("Open Projects", open_projects_count(REPO_ROOT))

        st.markdown("#### Platform Health")
        st.dataframe(module_table(), use_container_width=True)

        st.markdown("#### Knowledge Statistics")
        st.write(kstats)

        st.markdown("#### Recent Missions")
        if missions:
            st.dataframe(missions, use_container_width=True)
        else:
            st.info("No mission history found yet.")

        st.markdown("#### Latest Reports")
        if reports:
            st.dataframe(reports, use_container_width=True)
        else:
            st.info("No reports found.")

        st.markdown("#### Capability Map")
        st.dataframe(build_capability_map(), use_container_width=True)

        st.markdown("#### Running Jobs")
        st.info("SPOE autonomy loop, simulator jobs, and ingestion tasks are available through existing workbenches.")

        st.markdown("#### System Alerts")
        if str(coord.get("current_mode")) == "LOCAL EXECUTION MODE":
            st.warning("AI-FACTORY unavailable, running in LOCAL EXECUTION MODE.")
        else:
            st.success("AI-FACTORY online.")

        if st.button("Run Self Audit and Generate UI Status Report", type="primary"):
            report = run_self_audit(REPO_ROOT)
            out = write_html_report(report, REPO_ROOT / "ING_DIGHUB_UI_STATUS.html")
            st.success(f"Audit completed. Report generated: {out}")

    with right:
        st.subheader("Quick Actions")
        if st.button("Create Mission", use_container_width=True):
            _jump("pages/ing_dighub_mission_manager.py")
        if st.button("Analyze Plant", use_container_width=True):
            _jump("pages/plant_simulator.py")
        if st.button("Generate Report", use_container_width=True):
            _jump("pages/project_closeout.py")
        if st.button("Funding Consulting Center", use_container_width=True):
            _jump("pages/funding_consulting_center.py")
        if CONSULTING_HTML_REPORT.exists():
            if st.button("Open CTA Next Steps Report", use_container_width=True):
                _jump("pages/erp_profesional.py")
        if CONSULTING_QUICKSTART.exists():
            if st.button("Open Consultoria Quick Start", use_container_width=True):
                _jump("pages/erp_profesional.py")
        if st.button("Create Offer", use_container_width=True):
            _jump("pages/service_proposal_engine.py")
        if st.button("Open Knowledge Hub", use_container_width=True, key="quick_open_knowledge_hub"):
            _jump("pages/ing_dighub_knowledge_hub.py")
        if st.button("Search Engineering Assets", use_container_width=True):
            _jump("pages/document_analysis.py")
        if st.button("Launch Simulation", use_container_width=True):
            _jump("pages/reel_load_simulator_workbench.py")

        dwg = st.file_uploader("Upload DWG", type=["dwg", "dxf"])
        if dwg is not None:
            saved = _save_uploaded(dwg, REPO_ROOT / "knowledge_hub" / "outputs" / "uploads")
            st.success(f"DWG uploaded to: {saved}")

        doc = st.file_uploader("Upload Documentation", type=["pdf", "docx", "xlsx", "md", "txt"])
        if doc is not None:
            saved = _save_uploaded(doc, REPO_ROOT / "knowledge_hub" / "outputs" / "uploads")
            st.success(f"Documentation uploaded to: {saved}")

        if st.button("Compare Technologies", use_container_width=True):
            _jump("pages/competitive_intelligence.py")

        st.markdown("### Ask AI Coordinator")
        q = st.text_area("Question", placeholder="Ask for mission recommendations, capability status, or next engineering step.")
        if st.button("Ask", use_container_width=True):
            if str(coord.get("current_mode")) == "LOCAL EXECUTION MODE":
                st.info("LOCAL EXECUTION MODE active. Use mission manager actions to run autonomous loops.")
            elif q.strip():
                st.success("AI-FACTORY connected. Use Industrial Engineering Platform for direct module execution.")
            else:
                st.warning("Please enter a question.")


if __name__ == "__main__":
    main()
