"""Renderer 2D mejorado usando PIL para el simulador.
"""
from typing import Dict, Any
from PIL import Image, ImageDraw, ImageFont

PIXELS_PER_M = 10
CANVAS_W = 1200
CANVAS_H = 400


def _to_px(pos):
    x, y = pos
    return int(x * PIXELS_PER_M), int(y * PIXELS_PER_M)


def render_scene(snapshot: Dict[str, Any], layout: Dict[str, Any], scenario: str) -> Image.Image:
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

    # Warehouse
    wh = layout.get("warehouse")
    if wh:
        x, y = wh["pos"]
        w, h = wh["size"]
        x1, y1 = _to_px((x, y))
        x2, y2 = _to_px((x + w, y + h))
        draw.rectangle([x1, y1, x2, y2], outline="black", fill=(230, 220, 200))

    # Tracks
    tracks = layout.get("tracks", {})
    for tid, t in tracks.items():
        tx, ty = t["pos"]
        x1, y1 = _to_px((tx - 0.1, ty - 6))
        x2, y2 = _to_px((tx + 0.1, ty + 6))
        draw.rectangle([x1, y1, x2, y2], outline="black", fill=(180, 230, 180))

    # Scenario-specific zones
    if scenario == "forklift":
        bz = layout.get("buffer_zone")
        if bz:
            bx, by = bz["pos"]
            bw, bh = bz["size"]
            x1, y1 = _to_px((bx, by))
            x2, y2 = _to_px((bx + bw, by + bh))
            draw.rectangle([x1, y1, x2, y2], outline="black", fill=(255, 240, 160))
    else:
        ex = layout.get("exchange_zone")
        if ex:
            bx, by = ex["pos"]
            bw, bh = ex["size"]
            x1, y1 = _to_px((bx, by))
            x2, y2 = _to_px((bx + bw, by + bh))
            draw.rectangle([x1, y1, x2, y2], outline="black", fill=(255, 200, 120))

    # Entidades
    for e in snapshot.get("entities", []):
        ex, ey = e.get("pos", (0, 0))
        px, py = _to_px((ex, ey))
        if e.get("type") == "forklift":
            draw.rectangle([px - 8, py - 6, px + 8, py + 6], fill=(255, 200, 0))
            draw.text((px - 6, py - 10), "F")
        elif e.get("type") == "transfer":
            draw.rectangle([px - 12, py - 6, px + 12, py + 6], fill=(100, 150, 255))
            draw.text((px - 8, py - 10), "TR")

    # Bobinas
    reels = snapshot.get("reels", {})
    for rid, r in reels.items():
        rx, ry = r.get("pos", (0, 0))
        px, py = _to_px((rx, ry))
        color = (200, 50, 90) if r.get("status") == "in_warehouse" else (50, 150, 50)
        draw.ellipse([px - 6, py - 6, px + 6, py + 6], fill=color, outline=(0, 0, 0))

    return img
