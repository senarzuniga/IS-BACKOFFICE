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

    if "current_page" not in st.session_state:
        st.session_state.current_page = "command_center"

    st.sidebar.markdown("# 🎯 IS-BACKOFFICE")
    st.sidebar.markdown("---")


    page = st.sidebar.radio(
        "Navegación",
        [
            "🏠 Command Center",
            "🕵️ Inteligencia Web",
            "🖼️ Scraping",
            "📹 Medios",
            "🎨 INGECART ARTWORK",
            "🏭 Plant Simulator",
            "🏭 Smart Plant Dashboard",
            "⚙️ Configurar Smart Plant",
            "📋 Tareas",
            "🧾 Facturación ERP",
            "📊 Analytics",
        ],
        key="nav_radio",
    )


    page_map = {
        "🏠 Command Center": "command_center",
        "🕵️ Inteligencia Web": "intelligence",
        "🖼️ Scraping": "scraping",
        "📹 Medios": "media_upload",
        "🎨 INGECART ARTWORK": "ingecart_artwork",
        "🏭 Plant Simulator": "plant_simulator",
        "🏭 Smart Plant Dashboard": "smart_plant_dashboard",
        "⚙️ Configurar Smart Plant": "smart_plant_config",
        "📋 Tareas": "tasks",
        "🧾 Facturación ERP": "erp_facturacion",
        "📊 Analytics": "analytics",
    }

    st.session_state.current_page = page_map.get(page, "command_center")

    st.sidebar.markdown("---")
    st.sidebar.markdown("**📊 Estado**")

    if st.session_state.current_page == "command_center":
        _resolve_main()()

    elif st.session_state.current_page == "intelligence":
        from backoffice.ui.market_intelligence_panel import render_market_intelligence_panel
        render_market_intelligence_panel()

    elif st.session_state.current_page == "scraping":
        from backoffice.ui.scraping_panel import render_scraping_panel
        render_scraping_panel()

    elif st.session_state.current_page == "media_upload":
        from backoffice.ui.media_upload_panel import render_media_upload_panel
        render_media_upload_panel()

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

    elif st.session_state.current_page == "analytics":
        st.title("📊 Análisis y Reportes")
        st.markdown("*Funcionalidad de analítica en desarrollo*")
        st.info("Los reportes se generarán desde los datos disponibles")


if __name__ == "__main__":
    try:
        _create_enhanced_app()
    except Exception:
        _resolve_main()()