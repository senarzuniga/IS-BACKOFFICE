"""Renderizador simple para Streamlit usando st.canvas-like drawing via st.plotly_chart o st.pyplot.
Se mantiene sencillo: dibuja rectángulos, líneas y círculos en coordenadas del layout.
"""
from typing import Dict, Any
import math
import time

import streamlit as st
from PIL import Image, ImageDraw, ImageFont

PIXELS_PER_M = 10
CANVAS_W = 1200
CANVAS_H = 400


def _to_px(pos):
    x, y = pos
    return int(x * PIXELS_PER_M), int(y * PIXELS_PER_M)


def render_scene(state: Dict[str, Any], layout: Dict[str, Any], scenario: str) -> Image.Image:
    """Devuelve PIL Image con la escena renderizada.

    - state: salida de engine.get_state()
    - layout: layout del nivel
    - scenario: 'forklift' o 'ingetrans'
    """
    img = Image.new("RGBA", (CANVAS_W, CANVAS_H), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Dibujar corrugadora
    corr = layout.get("corrugator")
    if corr:
        x, y = corr["pos"]
        w, h = corr["size"]
        x1, y1 = _to_px((x, y))
        x2, y2 = _to_px((x + w, y + h))
        draw.rectangle([x1, y1, x2, y2], outline="black", fill=(200, 200, 220))
        draw.text((x1 + 5, y1 + 5), "Corrugadora", fill="black")

    # Dibujar warehouse
    wh = layout.get("warehouse")
    if wh:
        x, y = wh["pos"]
        w, h = wh["size"]
        x1, y1 = _to_px((x, y))
        x2, y2 = _to_px((x + w, y + h))
        draw.rectangle([x1, y1, x2, y2], outline="black", fill=(230, 220, 200))
        draw.text((x1 + 3, y1 + 3), "Warehouse", fill="black")

    # Dibujar tracks
    tracks = layout.get("tracks", {})
    for tid, t in tracks.items():
        tx, ty = t["pos"]
        x1, y1 = _to_px((tx - 0.1, ty - 6))
        x2, y2 = _to_px((tx + 0.1, ty + 6))
        draw.rectangle([x1, y1, x2, y2], outline="black", fill=(180, 230, 180))
        draw.text((x1 - 10, y1 - 12), tid, fill="black")

    # Scene entities
    for e in state.get("entities", []):
        ex, ey = e.get("pos", (0, 0))
        px, py = _to_px((ex, ey))
        if e.get("type") == "forklift":
            # dibujar como rectángulo con icono
            draw.rectangle([px - 8, py - 6, px + 8, py + 6], fill=(255, 200, 0))
            draw.text((px - 6, py - 10), "🚜")
        elif e.get("type") == "transfer":
            draw.rectangle([px - 12, py - 6, px + 12, py + 6], fill=(100, 150, 255))
            draw.text((px - 8, py - 10), "TR")

    # Bobinas
    for rid, r in state.get("reels", {}).items():
        rx, ry = r.get("pos", (0, 0))
        px, py = _to_px((rx, ry))
        color = (200, 50, 90) if r.get("status") == "in_warehouse" else (50, 150, 50)
        draw.ellipse([px - 6, py - 6, px + 6, py + 6], fill=color, outline=(0, 0, 0))

    return img


def display_in_streamlit(img, key=None):
    st.image(img, use_column_width=False, width=CANVAS_W)
