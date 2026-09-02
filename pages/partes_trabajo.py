"""Streamlit page for the standalone partes de trabajo portal."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


PORTAL_PATH = Path(__file__).resolve().parent.parent / "portal_partes.html"


def _load_portal_html() -> str:
    if not PORTAL_PATH.exists():
        raise FileNotFoundError(f"No se encuentra {PORTAL_PATH}")
    return PORTAL_PATH.read_text(encoding="utf-8")


def main() -> None:
    st.set_page_config(page_title="Partes y Proyectos", page_icon="⏱️", layout="wide")

    st.title("⏱️ Partes y Proyectos")
    st.caption(
        "Carga directamente la versión local de portal_partes.html para que el menú muestre siempre el contenido actualizado."
    )

    with st.sidebar:
        st.subheader("Actualización")
        if st.button("Recargar portal", use_container_width=True):
            st.rerun()

    html = _load_portal_html()
    modified_at = datetime.fromtimestamp(PORTAL_PATH.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    st.caption(f"Archivo cargado desde: {PORTAL_PATH.name} · última modificación detectada: {modified_at}")

    components.html(html, height=1800, scrolling=True)


if __name__ == "__main__":
    main()
