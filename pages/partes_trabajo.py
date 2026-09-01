from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from services.portal_partes_service import analyze_portal_partes, load_portal_partes_html, portal_partes_path


def _jump(page: str) -> None:
    st.switch_page(page)


@st.cache_data(show_spinner=False)
def _load_analysis():
    return analyze_portal_partes()


@st.cache_data(show_spinner=False)
def _load_portal_html() -> str:
    return load_portal_partes_html()


def main() -> None:
    st.set_page_config(page_title="Partes y Proyectos", page_icon="⏱️", layout="wide")

    try:
        from backoffice.theme import inject_theme

        inject_theme()
    except Exception:
        pass

    analysis = _load_analysis()
    portal_path = portal_partes_path()
    portal_html = _load_portal_html()

    st.title("⏱️ Portal de Partes, Tiempos y Proyectos")
    st.caption(
        "Integracion del portal HTML de partes dentro de IS-BACKOFFICE para registro de horas, control por OF/proyecto y analitica operativa."
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Pestañas funcionales", len(analysis.tabs))
    m2.metric("Categorias iniciales", analysis.default_category_count)
    m3.metric("Salidas operativas", len(analysis.reporting_outputs))
    m4.metric("Modo actual", "HTML integrado")

    app_tab, analysis_tab, roadmap_tab = st.tabs(
        ["Aplicacion integrada", "Analisis funcional", "Roadmap de integracion"]
    )

    with app_tab:
        st.info(
            "El portal original se ejecuta embebido para conservar su comportamiento actual. "
            "Las funciones de almacenamiento local, File System Access y ventanas emergentes dependen del navegador."
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Abrir ERP Profesional", use_container_width=True):
                _jump("pages/erp_profesional.py")
        with c2:
            if st.button("Abrir Project Closeout", use_container_width=True):
                _jump("pages/project_closeout.py")
        with c3:
            st.download_button(
                "Descargar HTML original",
                data=portal_html.encode("utf-8"),
                file_name=portal_path.name,
                mime="text/html",
                use_container_width=True,
            )

        components.html(portal_html, height=1900, scrolling=True)

    with analysis_tab:
        st.subheader("Resumen tecnico del HTML analizado")
        st.write(f"**Titulo detectado:** {analysis.title}")
        st.write(f"**Pestañas:** {', '.join(analysis.tabs)}")
        st.write(f"**Paneles internos:** {', '.join(analysis.panel_ids)}")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Capacidades identificadas")
            for item in analysis.capabilities:
                st.markdown(f"- {item}")

            st.markdown("#### Persistencia")
            for item in analysis.persistence_modes:
                st.markdown(f"- {item}")

        with c2:
            st.markdown("#### Maestros administrables")
            for item in analysis.admin_entities:
                st.markdown(f"- {item}")

            st.markdown("#### Reporting y exportacion")
            for item in analysis.reporting_outputs:
                st.markdown(f"- {item}")

        with st.expander("Categorias por defecto detectadas"):
            st.write(", ".join(analysis.default_categories))

        st.warning(
            "Arquitectonicamente, este portal sigue siendo una aplicacion cliente pura: no comparte usuarios, partes ni permisos con el backend FastAPI de IS-BACKOFFICE."
        )

    with roadmap_tab:
        st.markdown("#### Encaje en el ecosistema IS-BACKOFFICE")
        st.markdown(
            """
            - **ERP Profesional**: acceso operativo para carga diaria de horas y seguimiento de OF.
            - **Project Closeout**: reutilizable para cierres, incidencias y documentacion final de proyectos.
            - **Analytics / Reporting**: candidato a evolucionar hacia KPIs consolidados por proyecto, trabajador y desviacion vs. horas previstas.
            """
        )
        st.markdown("#### Siguiente evolucion recomendada")
        st.markdown(
            """
            1. Sustituir la persistencia JSON por API/backoffice con autenticacion centralizada.
            2. Compartir catalogos de trabajadores, proyectos y centros de coste con ERP.
            3. Añadir aprobacion de partes, estados y cierres semanales.
            4. Exponer desviaciones de horas previstas y avance de proyecto en dashboards ejecutivos.
            """
        )
        st.caption(f"Fuente analizada: {portal_path}")


if __name__ == "__main__":
    main()
