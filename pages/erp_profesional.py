from __future__ import annotations

from pathlib import Path

import streamlit as st

from backoffice.ui.components.consulting_brand import (
    CONSULTING_HTML_REPORT,
    CONSULTING_OFFER_SNIPPET,
    CONSULTING_QUICKSTART,
    CTA_BRAND_NAME,
    CTA_BRAND_TAGLINE,
    render_cta_brand_hero,
)


REPO_ROOT = Path(__file__).resolve().parent.parent


def _jump(page: str) -> None:
    st.switch_page(page)


def _download_html(label: str, path: Path) -> None:
    if not path.exists():
        st.info(f"No disponible todavia: {path.name}")
        return
    st.download_button(
        label,
        data=path.read_bytes(),
        file_name=path.name,
        mime="text/html",
        use_container_width=True,
    )


def main() -> None:
    st.set_page_config(page_title="ERP Profesional", page_icon="🧾", layout="wide")
    try:
        from backoffice.theme import inject_theme

        inject_theme()
    except Exception:
        pass

    render_cta_brand_hero(
        "ERP Profesional",
        "Nuevo modulo de acceso para Facturacion ERP, Funding Consulting Center y CTA R&D Funding Engine, con reporting y activos CTA reutilizables.",
        context_label=CTA_BRAND_NAME,
    )
    st.caption(CTA_BRAND_TAGLINE)

    metric_cols = st.columns(4)
    metric_cols[0].metric("Paneles unificados", 4)
    metric_cols[1].metric("Activos HTML", 4)
    metric_cols[2].metric("Ruta principal", "ERP -> Partes")
    metric_cols[3].metric("Estado", "Listo")

    module_tab, reporting_tab, offer_tab = st.tabs(["Modulo", "Reporting", "Oferta CTA"])

    with module_tab:
        st.subheader("Puntos de acceso del modulo")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                "<div class='cta-mini-card'><h4>Portal de Partes y Proyectos</h4><p>Registro de horas por trabajador, control por OF/proyecto y analitica operativa integrada.</p></div>",
                unsafe_allow_html=True,
            )
            if st.button("Abrir Portal de Partes", use_container_width=True):
                _jump("pages/partes_trabajo.py")
        with c2:
            st.markdown(
                "<div class='cta-mini-card'><h4>Facturacion ERP</h4><p>Gestion de clientes, facturas, cobros y reporting financiero anual.</p></div>",
                unsafe_allow_html=True,
            )
            if st.button("Abrir Facturacion ERP", use_container_width=True):
                _jump("pages/facturacion.py")
        with c3:
            st.markdown(
                "<div class='cta-mini-card'><h4>Funding Consulting Center</h4><p>Operacion consultiva para clasificar empresas, priorizar ayudas y preparar entregables.</p></div>",
                unsafe_allow_html=True,
            )
            if st.button("Abrir Funding Consulting Center", use_container_width=True):
                _jump("pages/funding_consulting_center.py")

        st.markdown(
            "<div class='cta-mini-card'><h4>CTA R&D Funding Engine</h4><p>Radar de convocatorias, matching proyecto-ayuda y seguimiento de readiness.</p></div>",
            unsafe_allow_html=True,
        )
        if st.button("Abrir CTA R&D Funding Engine", use_container_width=True):
            _jump("pages/rd_funding.py")

    with reporting_tab:
        st.subheader("Reporting y documentacion operativa")
        st.write("Desde este bloque se concentran los nuevos accesos documentales del modulo ERP Profesional.")
        d1, d2, d3 = st.columns(3)
        with d1:
            _download_html("Descargar informe HTML CTA", CONSULTING_HTML_REPORT)
        with d2:
            _download_html("Descargar guia rapida", CONSULTING_QUICKSTART)
        with d3:
            _download_html("Descargar snippet de oferta", CONSULTING_OFFER_SNIPPET)

        st.markdown("### Proximos pasos priorizados")
        st.markdown(
            """
            1. Crear imagen de marca CTA y reutilizarla en paneles, HTMLs y ofertas.
            2. Crear contenido comercial para diagnostico 360, sprint de 90 dias y modelo Fractional Sales Director.
            3. Lanzar busqueda de PYMES owner-led en Navarra con dolor claro en ventas, after-sales o KAM.
            4. Construir pipeline inicial y secuencia comercial por vertical.
            """
        )

    with offer_tab:
        st.subheader("Narrativa base CTA")
        st.markdown(
            """
            - **Posicionamiento**: Industrial Commercial Transformation Advisor.
            - **Promesa**: convertir estrategia comercial en ingresos medibles.
            - **Servicios iniciales**: diagnostico 360, programa de aceleracion comercial de 90 dias y direccion comercial fraccional.
            - **Diferenciador**: AI + data + ejecucion humana.
            """
        )


if __name__ == "__main__":
    main()
