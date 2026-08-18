"""IS-BACKOFFICE Streamlit entrypoint."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# If launched as a plain Python script, relaunch with `streamlit run`.
# Avoid importing Streamlit internals before this check to prevent bare-mode warnings.
if __name__ == "__main__" and "streamlit.web.bootstrap" not in sys.modules:
    script_path = str(Path(__file__).resolve())
    subprocess.run([sys.executable, "-m", "streamlit", "run", script_path], check=False)
    raise SystemExit(0)

import streamlit as st


def _resolve_main():
    """Resolve a callable UI entrypoint with safe fallbacks."""
    try:
        from backoffice.ui import command_center

        if hasattr(command_center, "main") and callable(command_center.main):
            return command_center.main

        if hasattr(command_center, "CommandCenter"):
            return lambda: command_center.CommandCenter().run()
    except Exception:
        pass

    # Fallback to legacy dashboard if the command center import fails.
    from backoffice.ui.app import main as legacy_main

    return legacy_main


def _create_enhanced_app():
    """Crea la aplicacion principal con integracion de scraping e inteligencia web."""

    st.set_page_config(
        page_title="IS-BACKOFFICE - AI Agentic Backoffice",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # ── Inject INGECART Design System ──────────────────────────────────────
    try:
        from backoffice.theme import inject_theme
        inject_theme()
    except Exception:
        pass
    # ──────────────────────────────────────────────────────────────────────

    if "current_page" not in st.session_state:
        st.session_state.current_page = "ing_dighub"

    st.sidebar.markdown("# 🎯 IS-BACKOFFICE")
    st.sidebar.markdown("---")


    page = st.sidebar.radio(
        "Navegación",
        [
            "🏭 ING_DIGHUB",
            "🏠 Command Center",
            "📚 Knowledge Hub",
            "🎯 Mission Manager",
            "🧭 Enterprise Digital Twin",
            "🏗️ Industrial Engineering Platform",
            "💶 R&D FUNDING",
            "📄 Service Proposal Engine",
            "🧠 Presentation Intelligence Engine",
            "📚 DIPC",
            "🧠 HTML Intelligence Studio",
            "🧩 SPOE Workbench",
            "🧠 Inteligencia de Conocimiento",
            "🕵️ Inteligencia Web",
            "🖼️ Scraping",
            "📹 Medios",
            "🔊 Transcripción",
            "🎨 INGECART ARTWORK",
            "🏭 Plant Simulator",
            "🏭 Smart Plant Dashboard",
            "⚙️ Configurar Smart Plant",
            "📋 Tareas",
            "🧾 Facturación ERP",
            "📁 Project Closeout",
            "📊 Analytics",
        ],
        key="nav_radio",
    )


    page_map = {
        "🏭 ING_DIGHUB": "ing_dighub",
        "🏠 Command Center": "command_center",
        "📚 Knowledge Hub": "ing_dighub_knowledge_hub",
        "🎯 Mission Manager": "ing_dighub_mission_manager",
        "🧭 Enterprise Digital Twin": "ing_dighub_digital_twin",
        "🏗️ Industrial Engineering Platform": "industrial_engineering_platform",
        "💶 R&D FUNDING": "rd_funding",
        "📄 Service Proposal Engine": "service_proposal_engine",
        "🧠 Presentation Intelligence Engine": "presentation_intelligence_engine",
        "📚 DIPC": "document_intelligence_publishing_center",
        "🧠 HTML Intelligence Studio": "html_intelligence_studio",
        "🧩 SPOE Workbench": "spoe_workbench",
        "🧠 Inteligencia de Conocimiento": "knowledge_intelligence",
        "🕵️ Inteligencia Web": "intelligence",
        "🖼️ Scraping": "scraping",
        "📹 Medios": "media_upload",
        "🔊 Transcripción": "audio_transcription",
        "🎨 INGECART ARTWORK": "ingecart_artwork",
        "🏭 Plant Simulator": "plant_simulator",
        "🏭 Smart Plant Dashboard": "smart_plant_dashboard",
        "⚙️ Configurar Smart Plant": "smart_plant_config",
        "📋 Tareas": "tasks",
        "🧾 Facturación ERP": "erp_facturacion",
        "📁 Project Closeout": "project_closeout",
        "📊 Analytics": "analytics",
    }

    st.session_state.current_page = page_map.get(page, "command_center")

    st.sidebar.markdown("---")
    st.sidebar.markdown("**📊 Estado**")

    if st.session_state.current_page == "ing_dighub":
        st.switch_page("pages/ing_dighub_home.py")

    elif st.session_state.current_page == "command_center":
        _resolve_main()()

    elif st.session_state.current_page == "ing_dighub_knowledge_hub":
        st.switch_page("pages/ing_dighub_knowledge_hub.py")

    elif st.session_state.current_page == "ing_dighub_mission_manager":
        st.switch_page("pages/ing_dighub_mission_manager.py")

    elif st.session_state.current_page == "ing_dighub_digital_twin":
        st.switch_page("pages/ing_dighub_digital_twin.py")

    elif st.session_state.current_page == "industrial_engineering_platform":
        st.switch_page("pages/industrial_engineering_platform.py")

    elif st.session_state.current_page == "rd_funding":
        st.switch_page("pages/rd_funding.py")

    elif st.session_state.current_page == "service_proposal_engine":
        st.switch_page("pages/service_proposal_engine.py")

    elif st.session_state.current_page == "presentation_intelligence_engine":
        st.switch_page("pages/presentation_intelligence_engine.py")

    elif st.session_state.current_page == "document_intelligence_publishing_center":
        st.switch_page("pages/document_intelligence_publishing_center.py")

    elif st.session_state.current_page == "html_intelligence_studio":
        st.switch_page("pages/html_intelligence_studio.py")

    elif st.session_state.current_page == "spoe_workbench":
        st.switch_page("pages/spoe_workbench.py")

    elif st.session_state.current_page == "intelligence":
        from backoffice.ui.market_intelligence_panel import render_market_intelligence_panel
        render_market_intelligence_panel()

    elif st.session_state.current_page == "knowledge_intelligence":
        try:
            from pages.knowledge_intelligence import main as knowledge_main
            knowledge_main()
        except Exception:
            st.error("No se puede cargar `pages/knowledge_intelligence.py`. Comprueba que el archivo existe.")

    elif st.session_state.current_page == "scraping":
        from backoffice.ui.scraping_panel import render_scraping_panel
        render_scraping_panel()

    elif st.session_state.current_page == "media_upload":
        from backoffice.ui.media_upload_panel import render_media_upload_panel
        render_media_upload_panel()

    elif st.session_state.current_page == "audio_transcription":
        from backoffice.ui.audio_transcription_panel import render_audio_transcription_panel
        render_audio_transcription_panel()

    elif st.session_state.current_page == "ingecart_artwork":
        st.switch_page("pages/ingecart_artwork.py")

    elif st.session_state.current_page == "plant_simulator":
        st.switch_page("pages/plant_simulator.py")
    elif st.session_state.current_page == "smart_plant_dashboard":
        # Llama al panel principal del Smart Plant Dashboard
        try:
            from pages.smart_plant_dashboard import main as smart_plant_main
            smart_plant_main()
        except Exception:
            st.error("No se puede cargar `pages/smart_plant_dashboard.py`. Comprueba que el archivo existe.")

    elif st.session_state.current_page == "smart_plant_config":
        # Llama al panel de configuración del Smart Plant Dashboard
        try:
            from pages.smart_plant_config import main as smart_plant_config_main
            smart_plant_config_main()
        except Exception:
            st.error("No se puede cargar `pages/smart_plant_config.py`. Comprueba que el archivo existe.")

    elif st.session_state.current_page == "tasks":
        st.title("📋 Gestión de Tareas")
        st.markdown("*Funcionalidad de tareas en desarrollo*")
        st.info("Los datos de tareas se cargarán desde la base de datos")


    elif st.session_state.current_page == "erp_facturacion":
        st.switch_page("pages/facturacion.py")

    elif st.session_state.current_page == "project_closeout":
        try:
            from pages.project_closeout import main as project_closeout_main
            project_closeout_main()
        except Exception as e:
            st.error("No se puede cargar `pages/project_closeout.py`. Comprueba que el archivo existe. Error: " + str(e))

    elif st.session_state.current_page == "analytics":
        st.title("📊 Análisis y Reportes")
        st.markdown("*Funcionalidad de analítica en desarrollo*")
        st.info("Los reportes se generarán desde los datos disponibles")


if __name__ == "__main__":
    try:
        _create_enhanced_app()
    except Exception:
        _resolve_main()()