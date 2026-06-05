"""Standalone INGECART artwork module page."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backoffice.ui.components.artwork import ARTWORK_OUTPUT_DIR, render_ingecart_artwork_block

st.set_page_config(page_title="INGECART ARTWORK", page_icon="🎨", layout="wide")

st.title("🎨 INGECART ARTWORK")
st.caption("Modulo visual de creatividades de marketing para INGECART.")

render_ingecart_artwork_block()

st.divider()
st.caption(f"Carpeta de salida por defecto: {ARTWORK_OUTPUT_DIR}")
