from typing import Dict


def render_plant_svg(engine) -> str:
    """Return a minimal SVG representation of the plant state.

    This is intentionally lightweight but provides a canvas-like string
    that can be embedded in Streamlit or HTML.
    """
    width = 800
    height = 300
    rect_w = 100
    rect_h = 40
    spacing = 10
    x = 10
    y = 10
    svg = [f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">']
    # Warehouse
    svg.append(f'<rect x="{x}" y="{y}" width="{rect_w}" height="{rect_h}" fill="#dfe6e9" stroke="#2d3436"/>')
    svg.append(f'<text x="{x+8}" y="{y+24}" fill="#2d3436">Warehouse: {sum(1 for t in engine.tracks if t["state"].name == "EMPTY")}</text>')
    # Buffer
    x += rect_w + spacing
    svg.append(f'<rect x="{x}" y="{y}" width="{rect_w}" height="{rect_h}" fill="#ffeaa7" stroke="#2d3436"/>')
    svg.append(f'<text x="{x+8}" y="{y+24}" fill="#2d3436">Buffer: {sum(1 for t in engine.tracks if t["state"].name == "FULL")}</text>')
    # Tracks (count)
    x += rect_w + spacing
    svg.append(f'<rect x="{x}" y="{y}" width="{rect_w}" height="{rect_h}" fill="#74b9ff" stroke="#2d3436"/>')
    svg.append(f'<text x="{x+8}" y="{y+24}" fill="#2d3436">Tracks occupied: {sum(1 for t in engine.tracks if t["state"].name not in ["EMPTY","RETURN_PENDING"])}</text>')
    # Corrugator
    x += rect_w + spacing
    svg.append(f'<rect x="{x}" y="{y}" width="{rect_w}" height="{rect_h}" fill="#55efc4" stroke="#2d3436"/>')
    svg.append(f'<text x="{x+8}" y="{y+24}" fill="#2d3436">Corrugator</text>')

    svg.append('</svg>')
    return "\n".join(svg)
