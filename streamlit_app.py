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
            "🏭 Plant Simulator",
            "📋 Tareas",
            "🧾 Facturas",
            "📊 Analytics",
        ],
        key="nav_radio",
    )

    page_map = {
        "🏠 Command Center": "command_center",
        "🕵️ Inteligencia Web": "intelligence",
        "🖼️ Scraping": "scraping",
        "🏭 Plant Simulator": "plant_simulator",
        "📋 Tareas": "tasks",
        "🧾 Facturas": "invoices",
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

    elif st.session_state.current_page == "plant_simulator":
        st.switch_page("pages/plant_simulator.py")

    elif st.session_state.current_page == "tasks":
        st.title("📋 Gestión de Tareas")
        st.markdown("*Funcionalidad de tareas en desarrollo*")
        st.info("Los datos de tareas se cargarán desde la base de datos")

    elif st.session_state.current_page == "invoices":
        st.title("🧾 Facturas")
        st.markdown("*Funcionalidad de facturación en desarrollo*")
        st.info("Los datos de facturas se cargarán desde la base de datos")

    elif st.session_state.current_page == "analytics":
        st.title("📊 Análisis y Reportes")
        st.markdown("*Funcionalidad de analítica en desarrollo*")
        st.info("Los reportes se generarán desde los datos disponibles")


if __name__ == "__main__":
    try:
        _create_enhanced_app()
    except Exception:
        _resolve_main()()