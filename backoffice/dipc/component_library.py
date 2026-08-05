from __future__ import annotations

import html
from collections import Counter
from typing import Any

from .models import ComponentNode, ComponentKind


_KEYWORD_MAP: list[tuple[set[str], ComponentKind]] = [
    ({"timeline", "roadmap", "milestone", "phase"}, "timeline"),
    ({"process", "workflow", "flow", "step"}, "process_flow"),
    ({"pyramid", "layer", "maturity"}, "pyramid"),
    ({"cycle", "loop", "continuous improvement"}, "cycle"),
    ({"matrix", "quadrant"}, "matrix"),
    ({"relationship", "relationship map", "ecosystem"}, "relationship"),
    ({"chevron", "journey"}, "chevron"),
    ({"hierarchy", "organization", "org chart"}, "hierarchy"),
    ({"dashboard", "kpi", "scorecard"}, "executive_dashboard"),
    ({"risk", "severity", "impact"}, "risk_matrix"),
    ({"roi", "payback", "investment"}, "roi_summary"),
    ({"digital twin"}, "digital_twin_panel"),
    ({"amr"}, "amr_fleet_panel"),
    ({"ingetrans", "reel"}, "ingetrans_panel"),
]


def infer_component_kind(title: str, body: str, fallback: ComponentKind = "text") -> ComponentKind:
    haystack = f"{title} {body}".lower()
    for keywords, component_kind in _KEYWORD_MAP:
        if any(keyword in haystack for keyword in keywords):
            return component_kind
    return fallback


def normalize_component(kind: ComponentKind, title: str | None, body: str | None, items: list[dict[str, Any]] | None = None, props: dict[str, Any] | None = None) -> ComponentNode:
    return ComponentNode(
        component_kind=kind,
        title=title,
        body=body,
        items=items or [],
        props=props or {},
    )


def render_component(component: ComponentNode) -> str:
    renderer = _RENDERERS.get(component.component_kind, _render_text)
    return renderer(component)


def summarize_component_usage(components: list[ComponentNode]) -> dict[str, int]:
    counter = Counter(component.component_kind for component in components)
    return dict(counter)


def _render_text(component: ComponentNode) -> str:
    title = f"<h3>{html.escape(component.title)}</h3>" if component.title else ""
    body = f"<p>{html.escape(component.body or '')}</p>" if component.body else ""
    return f"<section class='dipc-component text-block'>{title}{body}</section>"


def _render_feature_cards(component: ComponentNode) -> str:
    cards = []
    for item in component.items:
        cards.append(
            "<article class='dipc-card'>"
            f"<h4>{html.escape(str(item.get('title', 'Card')))}</h4>"
            f"<p>{html.escape(str(item.get('body', '')))}</p>"
            "</article>"
        )
    return f"<section class='dipc-component feature-cards'><div class='dipc-card-grid'>{''.join(cards)}</div></section>"


def _render_table(component: ComponentNode) -> str:
    rows = component.props.get('rows', [])
    if not rows:
        return _render_text(component)
    head = rows[0]
    body = rows[1:]
    return (
        "<section class='dipc-component comparison-table'>"
        "<div class='dipc-table-wrap'><table><thead><tr>"
        + "".join(f"<th>{html.escape(str(cell))}</th>" for cell in head)
        + "</tr></thead><tbody>"
        + "".join("<tr>" + "".join(f"<td>{html.escape(str(cell))}</td>" for cell in row) + "</tr>" for row in body)
        + "</tbody></table></div></section>"
    )


def _render_kpis(component: ComponentNode) -> str:
    cards = []
    for item in component.items:
        cards.append(
            "<article class='dipc-kpi'>"
            f"<span>{html.escape(str(item.get('label', 'KPI')))}</span>"
            f"<strong>{html.escape(str(item.get('value', '')))}</strong>"
            f"<small>{html.escape(str(item.get('detail', '')))}</small>"
            "</article>"
        )
    return f"<section class='dipc-component industrial-kpi'><div class='dipc-kpi-grid'>{''.join(cards)}</div></section>"


def _render_timeline(component: ComponentNode) -> str:
    items = component.items or [{"title": component.title or "Step", "body": component.body or ""}]
    nodes = []
    for idx, item in enumerate(items):
        x = 80 + idx * 220
        nodes.append(
            f"<g><circle cx='{x}' cy='40' r='20'></circle><text x='{x}' y='45' text-anchor='middle'>{idx + 1}</text></g>"
            f"<foreignObject x='{x - 80}' y='70' width='160' height='120'><div xmlns='http://www.w3.org/1999/xhtml' class='dipc-svg-card'><strong>{html.escape(str(item.get('title', '')))}</strong><p>{html.escape(str(item.get('body', '')))}</p></div></foreignObject>"
        )
    connectors = "".join(f"<line x1='{190 + idx * 220}' y1='40' x2='{(idx + 1) * 220 + 80 - 30}' y2='40'></line>" for idx in range(max(len(items) - 1, 0)))
    width = max(300, 80 + len(items) * 220)
    return f"<section class='dipc-component timeline'><svg viewBox='0 0 {width} 220'>{connectors}{''.join(nodes)}</svg></section>"


def _render_process_flow(component: ComponentNode) -> str:
    items = component.items or [{"title": component.title or "Process", "body": component.body or ""}]
    steps = []
    for idx, item in enumerate(items):
        steps.append(f"<div class='dipc-chevron'><span>{idx + 1}</span><strong>{html.escape(str(item.get('title', '')))}</strong><p>{html.escape(str(item.get('body', '')))}</p></div>")
    return f"<section class='dipc-component process-flow'><div class='dipc-chevron-row'>{''.join(steps)}</div></section>"


def _render_pyramid(component: ComponentNode) -> str:
    items = component.items or [{"title": component.title or "Layer", "body": component.body or ""}]
    levels = []
    total = len(items)
    for idx, item in enumerate(reversed(items), start=1):
        width = 30 + (idx * 14)
        levels.append(f"<div class='dipc-pyramid-level' style='width:{width}%;'><strong>{html.escape(str(item.get('title', '')))}</strong><span>{html.escape(str(item.get('body', '')))}</span></div>")
    return f"<section class='dipc-component pyramid'><div class='dipc-pyramid'>{''.join(levels)}</div></section>"


def _render_cycle(component: ComponentNode) -> str:
    items = component.items or [{"title": component.title or "Cycle", "body": component.body or ""}]
    total = len(items)
    if total == 1:
        total = 2
        items = items + items
    parts = []
    for idx, item in enumerate(items):
        angle = (360 / total) * idx
        parts.append(f"<div class='dipc-cycle-item' style='transform: rotate({angle}deg) translateY(-150px) rotate(-{angle}deg);'><strong>{html.escape(str(item.get('title', '')))}</strong></div>")
    return f"<section class='dipc-component cycle'><div class='dipc-cycle-core'>Continuous Improvement</div><div class='dipc-cycle'>{''.join(parts)}</div></section>"


def _render_matrix(component: ComponentNode) -> str:
    items = component.items or []
    cells = []
    for item in items[:4]:
        cells.append(f"<div class='dipc-matrix-cell'><strong>{html.escape(str(item.get('title', '')))}</strong><p>{html.escape(str(item.get('body', '')))}</p></div>")
    return f"<section class='dipc-component matrix'><div class='dipc-matrix-grid'>{''.join(cells)}</div></section>"


def _render_relationship(component: ComponentNode) -> str:
    items = component.items or []
    center = component.title or 'Core'
    satellites = []
    for idx, item in enumerate(items[:6]):
        satellites.append(f"<div class='dipc-relationship-node n{idx + 1}'><strong>{html.escape(str(item.get('title', '')))}</strong></div>")
    return f"<section class='dipc-component relationship'><div class='dipc-relationship-core'>{html.escape(center)}</div>{''.join(satellites)}</section>"


def _render_hierarchy(component: ComponentNode) -> str:
    items = component.items or []
    if not items:
        items = [{"title": component.title or 'Root', "body": component.body or ''}]
    root = items[0]
    children = items[1:]
    child_html = ''.join(f"<div class='dipc-tree-child'><strong>{html.escape(str(item.get('title', '')))}</strong><p>{html.escape(str(item.get('body', '')))}</p></div>" for item in children)
    return f"<section class='dipc-component hierarchy'><div class='dipc-tree-root'><strong>{html.escape(str(root.get('title', 'Root')))}</strong><p>{html.escape(str(root.get('body', '')))}</p></div><div class='dipc-tree-children'>{child_html}</div></section>"


def _render_dashboard(component: ComponentNode) -> str:
    header = f"<h3>{html.escape(component.title)}</h3>" if component.title else ""
    charts = _render_kpis(component)
    return f"<section class='dipc-component executive-dashboard'>{header}{charts}</section>"


def _render_contact(component: ComponentNode) -> str:
    return (
        "<section class='dipc-component contact-block'>"
        f"<h3>{html.escape(component.title or 'Contact')}</h3>"
        f"<p>{html.escape(component.body or '')}</p>"
        "</section>"
    )


def _render_footer(component: ComponentNode) -> str:
    return f"<footer class='dipc-component footer'><p>{html.escape(component.body or component.title or 'Generated by DIPC')}</p></footer>"


_RENDERERS = {
    "text": _render_text,
    "hero": _render_text,
    "executive_summary": _render_text,
    "feature_cards": _render_feature_cards,
    "comparison_table": _render_table,
    "table": _render_table,
    "industrial_kpi": _render_kpis,
    "executive_dashboard": _render_dashboard,
    "timeline": _render_timeline,
    "process_flow": _render_process_flow,
    "project_roadmap": _render_timeline,
    "pyramid": _render_pyramid,
    "cycle": _render_cycle,
    "matrix": _render_matrix,
    "risk_matrix": _render_matrix,
    "relationship": _render_relationship,
    "chevron": _render_process_flow,
    "hierarchy": _render_hierarchy,
    "org_chart": _render_hierarchy,
    "mission_cards": _render_feature_cards,
    "digital_twin_panel": _render_feature_cards,
    "factory_layout": _render_feature_cards,
    "technical_specification": _render_feature_cards,
    "engineering_drawing_viewer": _render_feature_cards,
    "amr_fleet_panel": _render_feature_cards,
    "ingetrans_panel": _render_feature_cards,
    "maintenance_report": _render_feature_cards,
    "business_case": _render_feature_cards,
    "roi_summary": _render_kpis,
    "contact_block": _render_contact,
    "footer": _render_footer,
    "infographic": _render_feature_cards,
    "image_gallery": _render_feature_cards,
}
