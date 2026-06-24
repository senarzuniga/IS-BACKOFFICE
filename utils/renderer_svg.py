"""Renderizado SVG con animación fluida, colores de estado, flujos y heatmap.

Este módulo genera una escena SVG a partir de un 'snapshot' devuelto
por los motores de simulación (BaseSimulationEngine.get_snapshot()).
Está diseñado para ser seguro y de dependencia mínima para incrustar
HTML/SVG en Streamlit con `components.v1.html(svg_string, height=...)`.
"""
from typing import Dict, List, Any
import math

# Mapa de colores según estado
STATE_COLORS = {
    "idle": "#48bb78",          # Verde
    "moving": "#63b3ed",        # Azul
    "handling": "#f6ad55",      # Naranja
    "blocked": "#fc8181",       # Rojo
    "maintenance": "#9f7aea",   # Morado
    "waiting_operator": "#f687b3", # Rosa
    "returning": "#d53f8c",     # Magenta
    "idle_low": "#48bb78",
    "idle_medium": "#ecc94b",
    "idle_high": "#fc8181",
}


def get_utilization_color(utilization: float) -> str:
    """Devuelve color según nivel de utilización (0..1)."""
    try:
        u = float(utilization)
    except Exception:
        return "#48bb78"
    if u < 0.70:
        return "#48bb78"  # Verde
    elif u < 0.90:
        return "#ecc94b"  # Amarillo
    else:
        return "#fc8181"  # Rojo


def _safe(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default


def render_svg_scene(snapshot: Dict[str, Any], scenario_label: str, width: int = 900, height: int = 520) -> str:
    """Genera un SVG completo con todos los elementos animados.

    snapshot: dict proveniente de `BaseSimulationEngine.get_snapshot()`.
    Se adapta a la forma esperada: contiene 'time_min', 'entities', 'reels', 'metrics', 'queue_len'.
    """
    # Extraer datos del snapshot con nombres compatibles
    time_min = _safe(snapshot.get("time_min", snapshot.get("time", 0.0)))
    resources = snapshot.get("entities", []) or snapshot.get("resources", [])
    reels = snapshot.get("reels", {})
    metrics = snapshot.get("metrics", {}) or {}
    buffer_count = int(sum(1 for r in (reels.values() if isinstance(reels, dict) else []) if r.get("status") == "in_buffer"))
    buffer_capacity = int(metrics.get("buffer_capacity", metrics.get("buffer_cap", 8)))
    queue_length = int(snapshot.get("queue_len", snapshot.get("queue_length", 0)))

    # KPIs
    kpis = snapshot.get("kpis", {}) or metrics
    lpi = _safe(kpis.get("lpi", metrics.get("lpi", 50)))

    # Track occupancy: derivar cantidad de tracks ocupados a partir de reels en track
    occupied_tracks = int(sum(1 for r in (reels.values() if isinstance(reels, dict) else []) if r.get("status") == "on_track"))
    total_tracks = int(metrics.get("num_tracks", 10)) or 10

    # Calcular tráfico y color
    traffic_level = (occupied_tracks / max(1, total_tracks)) * 0.5 + (buffer_count / max(1, buffer_capacity)) * 0.5
    if traffic_level < 0.3:
        traffic_color = "#48bb78"
    elif traffic_level < 0.6:
        traffic_color = "#ecc94b"
    else:
        traffic_color = "#fc8181"

    stroke_width = 2 + traffic_level * 6

    # Utilización principal (usar dict de utilization_minutes o utilization_pct)
    util_vals = []
    util_dict = kpis.get("utilization_pct") or kpis.get("utilization") or metrics.get("utilization_pct") or metrics.get("utilization_time_min")
    if isinstance(util_dict, dict):
        for v in util_dict.values():
            try:
                vv = float(v)
                # si son minutos, normalizar por time_min
                if vv > 100 and time_min > 0:
                    vv = (vv / time_min)  # rough normalize to percent-like scale
                util_vals.append(min(100.0, vv))
            except Exception:
                pass
    main_util = sum(util_vals) / len(util_vals) if util_vals else 0.0

    # Escala de visualización para coordenadas del layout
    scale = 6.0
    x_offset = 80
    y_offset = 120

    # Inicio del SVG
    svg = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="heatmap" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" style="stop-color:#48bb78;stop-opacity:0.3" />
                <stop offset="50%" style="stop-color:#ecc94b;stop-opacity:0.5" />
                <stop offset="100%" style="stop-color:#fc8181;stop-opacity:0.8" />
            </linearGradient>
            <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#2d3748" stroke-width="0.5" opacity="0.3"/>
            </pattern>
            <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="2" dy="2" stdDeviation="3" flood-color="#000" flood-opacity="0.3"/>
            </filter>
            <marker id="arrow_green" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#48bb78" /></marker>
            <marker id="arrow_yellow" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#ecc94b" /></marker>
            <marker id="arrow_red" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#fc8181" /></marker>
        </defs>
        <rect width="{width}" height="{height}" fill="#1a202c" rx="8"/>
        <rect width="{width}" height="{height}" fill="url(#grid)"/>
        <text x="20" y="30" fill="#a0aec0" font-family="Arial" font-size="14" font-weight="bold">Escenario {scenario_label} · Tiempo: {time_min:.1f} min</text>

        <!-- Warehouse -->
        <rect x="20" y="60" width="100" height="350" fill="#2d3748" stroke="#4a5568" stroke-width="1.5" rx="6"/>
        <text x="30" y="85" fill="#a0aec0" font-family="Arial" font-size="12" font-weight="bold">WAREHOUSE</text>

        <!-- Buffer -->
        <rect x="150" y="60" width="80" height="350" fill="#2d3748" stroke="#4a5568" stroke-width="1.5" rx="6" opacity="0.6"/>
        <text x="160" y="85" fill="#a0aec0" font-family="Arial" font-size="11">BUFFER</text>
        <rect x="160" y="360" width="60" height="15" fill="#1a202c" rx="3"/>
        <rect x="160" y="360" width="{min(60, (buffer_count/buffer_capacity)*60 if buffer_capacity>0 else 0)}" height="15" fill="{get_utilization_color(buffer_count/max(1,buffer_capacity))}" rx="3"/>
        <text x="190" y="372" fill="white" font-family="Arial" font-size="9" text-anchor="middle">{buffer_count}/{buffer_capacity}</text>

        <!-- Exchange and Rail -->
        <rect x="250" y="60" width="80" height="350" fill="#2d3748" stroke="#4a5568" stroke-width="1.5" rx="6" opacity="0.6"/>
        <text x="260" y="85" fill="#a0aec0" font-family="Arial" font-size="11">EXCHANGE</text>
        <line x1="330" y1="235" x2="550" y2="235" stroke="#fc8181" stroke-width="4" stroke-dasharray="8,4"/>
        <text x="440" y="225" fill="#fc8181" font-family="Arial" font-size="10">RAIL</text>

        <!-- Corrugadora/Tracks -->
        <rect x="700" y="60" width="180" height="350" fill="#2d3748" stroke="#4a5568" stroke-width="1.5" rx="6"/>
        <text x="710" y="85" fill="#a0aec0" font-family="Arial" font-size="12" font-weight="bold">CORRUGADORA</text>
    '''

    # Dibujar tracks (marcar los primeros occupied_tracks como ocupados)
    for i in range(total_tracks):
        x = 710 + (i % 5) * 32
        y = 110 + (i // 5) * 150
        is_occupied = i < occupied_tracks
        color = "#fc8181" if False else ("#ecc94b" if is_occupied else "#48bb78")
        svg += f"""
        <rect x="{x}" y="{y}" width="16" height="120" fill="{color}" stroke="#1a202c" stroke-width="1" rx="3"/>
        <text x="{x+8}" y="{y-8}" fill="#a0aec0" font-family="Arial" font-size="8" text-anchor="middle">T{i+1}</text>
        """

    # Recursos dinámicos (entidades)
    for resource in resources:
        pos = resource.get("pos") or resource.get("position") or (0, 0)
        try:
            rx = float(pos[0]) * scale + x_offset
            ry = float(pos[1]) * scale + y_offset
        except Exception:
            rx = x_offset
            ry = y_offset
        state = resource.get("state", "idle")
        loaded = resource.get("loaded", False) or bool(resource.get("task"))
        resource_id = resource.get("id", resource.get("name", "R-?"))

        color = STATE_COLORS.get(state, "#a0aec0")
        if resource.get("type", "") == "transfer":
            svg += f"""
            <g filter="url(#shadow)">
                <rect x="{rx-28}" y="{ry-10}" width="56" height="20" rx="6" fill="{color}" stroke="#1a202c" stroke-width="2"/>
                <text x="{rx}" y="{ry+4}" fill="white" font-family="Arial" font-size="9" font-weight="bold" text-anchor="middle">TRANSFER</text>
            </g>
            """
            if loaded:
                svg += f"""
                <circle cx="{rx-12}" cy="{ry-22}" r="8" fill="#fc8181" stroke="#1a202c" stroke-width="1.5"/>
                <circle cx="{rx+12}" cy="{ry-22}" r="8" fill="#fc8181" stroke="#1a202c" stroke-width="1.5"/>
                """
        else:
            svg += f"""
            <g filter="url(#shadow)">
                <rect x="{rx-18}" y="{ry-12}" width="36" height="24" rx="4" fill="{color}" stroke="#1a202c" stroke-width="2"/>
                <text x="{rx}" y="{ry+4}" fill="white" font-family="Arial" font-size="9" font-weight="bold" text-anchor="middle">{resource_id}</text>
            </g>
            """
            if loaded:
                svg += f"""
                <circle cx="{rx}" cy="{ry-20}" r="10" fill="#fc8181" stroke="#1a202c" stroke-width="1.5"/>
                <text x="{rx}" y="{ry-17}" fill="white" font-size="8" text-anchor="middle">📦</text>
                """

    # Líneas de flujo
    marker = "#arrow_green" if traffic_color == "#48bb78" else ("#arrow_yellow" if traffic_color == "#ecc94b" else "#arrow_red")
    svg += f"""
    <line x1="120" y1="235" x2="150" y2="235" stroke="{traffic_color}" stroke-width="{stroke_width}" marker-end="url({marker})" opacity="0.7"/>
    <line x1="330" y1="235" x2="700" y2="235" stroke="{traffic_color}" stroke-width="{stroke_width}" marker-end="url({marker})" opacity="0.5"/>
    """

    # Heatmap overlays
    svg += f"""
    <rect x="20" y="60" width="100" height="350" fill="url(#heatmap)" opacity="{min(0.9, (main_util/100.0)*0.3)}" rx="6"/>
    <rect x="150" y="60" width="80" height="350" fill="url(#heatmap)" opacity="{min(0.9, (buffer_count/max(1,buffer_capacity))*0.4)}" rx="6"/>
    <rect x="700" y="60" width="180" height="350" fill="url(#heatmap)" opacity="{min(0.9, (occupied_tracks/max(1,total_tracks))*0.3)}" rx="6"/>
    """

    # KPI panel and saturation bar
    util_color = get_utilization_color(main_util / 100.0)
    svg += f"""
    <rect x="{width-220}" y="10" width="200" height="50" fill="#1a202c" stroke="#4a5568" stroke-width="1" rx="6" opacity="0.9"/>
    <text x="{width-210}" y="30" fill="#a0aec0" font-family="Arial" font-size="10">Logistic Pressure Index (LPI)</text>
    <text x="{width-210}" y="50" fill="{('#48bb78' if lpi < 40 else '#ecc94b' if lpi < 70 else '#fc8181')}" font-family="Arial" font-size="18" font-weight="bold">{lpi:.0f}</text>
    <text x="{width-60}" y="50" fill="#a0aec0" font-family="Arial" font-size="10">/ 100</text>
    <rect x="20" y="{height-30}" width="200" height="16" fill="#1a202c" rx="8"/>
    <rect x="20" y="{height-30}" width="{min(200, main_util * 2)}" height="16" fill="{util_color}" rx="8"/>
    <text x="120" y="{height-17}" fill="white" font-family="Arial" font-size="9" text-anchor="middle">Utilización: {main_util:.1f}%</text>
    <text x="700" y="430" fill="#a0aec0" font-family="Arial" font-size="11">📋 Cola de trabajos: {queue_length}</text>
    """

    # Leyenda
    svg += f"""
    <rect x="20" y="470" width="12" height="12" fill="#48bb78" rx="2"/>
    <text x="36" y="480" fill="#a0aec0" font-family="Arial" font-size="9">Disponible</text>
    <rect x="100" y="470" width="12" height="12" fill="#ecc94b" rx="2"/>
    <text x="116" y="480" fill="#a0aec0" font-family="Arial" font-size="9">Ocupado</text>
    <rect x="180" y="470" width="12" height="12" fill="#fc8181" rx="2"/>
    <text x="196" y="480" fill="#a0aec0" font-family="Arial" font-size="9">Saturado</text>
    <rect x="260" y="470" width="12" height="12" fill="#63b3ed" rx="2"/>
    <text x="276" y="480" fill="#a0aec0" font-family="Arial" font-size="9">En movimiento</text>
    <rect x="340" y="470" width="12" height="12" fill="#9f7aea" rx="2"/>
    <text x="356" y="480" fill="#a0aec0" font-family="Arial" font-size="9">Retorno</text>
    <rect x="420" y="470" width="12" height="12" fill="#fc8181" rx="2"/>
    <text x="436" y="480" fill="#a0aec0" font-family="Arial" font-size="9">Avería</text>
    </svg>"""

    return svg
