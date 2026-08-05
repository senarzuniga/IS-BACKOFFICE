from __future__ import annotations

from typing import Any

from backoffice.theme.design_system import DARK, INDUSTRIAL, LIGHT, Theme

from .models import ThemeVariant


HIGH_CONTRAST = Theme(
    bg_primary="#000000",
    bg_surface="#0A0A0A",
    bg_card="#111111",
    bg_sidebar="#000000",
    bg_header="#000000",
    bg_elevated="#111111",
    bg_input="#111111",
    bg_table_row="#101010",
    bg_hover="#1D1D1D",
    border_subtle="#3A3A3A",
    border_default="#5A5A5A",
    border_strong="#8A8A8A",
    border_focus="#FFD400",
    text_primary="#FFFFFF",
    text_secondary="#E2E2E2",
    text_disabled="#9A9A9A",
    text_inverse="#000000",
    accent="#FFD400",
    accent_hover="#FFE870",
    accent_dark="#D0A800",
    accent_muted="rgba(255,212,0,0.18)",
    success="#52FF8B",
    success_muted="rgba(82,255,139,0.15)",
    warning="#FFD400",
    warning_muted="rgba(255,212,0,0.15)",
    error="#FF6B6B",
    error_muted="rgba(255,107,107,0.15)",
    info="#66CCFF",
    info_muted="rgba(102,204,255,0.15)",
    link="#FFD400",
    shadow="rgba(0,0,0,0.7)",
    chart_grid="#444444",
    chart_axis="#888888",
    metric_value="#FFD400",
    btn_primary_bg="#FFD400",
    btn_primary_text="#000000",
    btn_secondary_bg="#111111",
    btn_secondary_text="#FFFFFF",
    badge_bg="rgba(255,212,0,0.20)",
    badge_text="#FFD400",
)


def get_theme(variant: ThemeVariant) -> Theme:
    return {
        "industrial": INDUSTRIAL,
        "light": LIGHT,
        "dark": DARK,
        "high_contrast": HIGH_CONTRAST,
    }[variant]


def build_theme_tokens(variant: ThemeVariant, palette: list[str] | None = None) -> dict[str, Any]:
    theme = get_theme(variant)
    tokens = theme.as_dict()
    tokens.update(
        {
            "palette": palette or [tokens["accent"], tokens["bg_primary"], tokens["bg_surface"], tokens["text_primary"]],
            "typography": {
                "headline": "Montserrat, Segoe UI, Arial, sans-serif",
                "body": "Inter, Segoe UI, Arial, sans-serif",
                "mono": "Consolas, Courier New, monospace",
            },
            "spacing": {"2xs": "0.125rem", "xs": "0.25rem", "sm": "0.5rem", "md": "1rem", "lg": "1.5rem", "xl": "2.5rem", "2xl": "4rem"},
            "grid": {"content_max": "1280px", "sidebar_width": "290px", "gutter": "24px"},
            "breakpoints": {"mobile": 768, "tablet": 1024, "desktop": 1440},
            "animations": {
                "fade_in": "320ms ease",
                "stagger": "60ms",
                "panel": "420ms cubic-bezier(0.2, 0.8, 0.2, 1)",
            },
            "iconography": {"stroke": 1.75, "radius": 12},
        }
    )
    return tokens


def build_css(variant: ThemeVariant, palette: list[str] | None = None) -> str:
    tokens = build_theme_tokens(variant, palette)
    return f"""
:root {{
  --dipc-bg-primary: {tokens['bg_primary']};
  --dipc-bg-surface: {tokens['bg_surface']};
  --dipc-bg-card: {tokens['bg_card']};
  --dipc-bg-sidebar: {tokens['bg_sidebar']};
  --dipc-bg-elevated: {tokens['bg_elevated']};
  --dipc-text-primary: {tokens['text_primary']};
  --dipc-text-secondary: {tokens['text_secondary']};
  --dipc-border-default: {tokens['border_default']};
  --dipc-border-strong: {tokens['border_strong']};
  --dipc-accent: {tokens['accent']};
  --dipc-accent-hover: {tokens['accent_hover']};
  --dipc-accent-muted: {tokens['accent_muted']};
  --dipc-success: {tokens['success']};
  --dipc-warning: {tokens['warning']};
  --dipc-error: {tokens['error']};
  --dipc-headline: {tokens['typography']['headline']};
  --dipc-body: {tokens['typography']['body']};
  --dipc-mono: {tokens['typography']['mono']};
  --dipc-space-xs: {tokens['spacing']['xs']};
  --dipc-space-sm: {tokens['spacing']['sm']};
  --dipc-space-md: {tokens['spacing']['md']};
  --dipc-space-lg: {tokens['spacing']['lg']};
  --dipc-space-xl: {tokens['spacing']['xl']};
  --dipc-space-2xl: {tokens['spacing']['2xl']};
  --dipc-content-max: {tokens['grid']['content_max']};
  --dipc-sidebar-width: {tokens['grid']['sidebar_width']};
  --dipc-shadow: 0 18px 42px rgba(0,0,0,0.25);
}}

* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--dipc-bg-primary); color: var(--dipc-text-primary); font-family: var(--dipc-body); }}
a {{ color: var(--dipc-accent); }}
.dipc-lang-switch {{ position: sticky; top: 0; z-index: 12; display: flex; align-items: center; gap: 0.45rem; padding: 0.55rem 0.85rem; background: var(--dipc-bg-elevated); border-bottom: 1px solid var(--dipc-border-default); }}
.dipc-lang-switch span {{ color: var(--dipc-text-secondary); font-size: 0.85rem; }}
.dipc-lang-switch button {{ border: 1px solid var(--dipc-border-default); background: var(--dipc-bg-card); color: var(--dipc-text-primary); border-radius: 999px; padding: 0.28rem 0.68rem; cursor: pointer; }}
.dipc-lang-switch button:hover {{ border-color: var(--dipc-accent); color: var(--dipc-accent); }}
main {{ max-width: var(--dipc-content-max); margin: 0 auto; padding: var(--dipc-space-lg); }}
.dipc-shell {{ display: grid; grid-template-columns: minmax(220px, var(--dipc-sidebar-width)) minmax(0, 1fr); min-height: 100vh; }}
.dipc-sidebar {{ position: sticky; top: 0; align-self: start; height: 100vh; padding: var(--dipc-space-lg); background: var(--dipc-bg-sidebar); border-right: 1px solid var(--dipc-border-default); overflow-y: auto; }}
.dipc-sidebar a {{ display: block; color: var(--dipc-text-secondary); text-decoration: none; padding: 0.45rem 0.65rem; border-radius: 10px; margin-bottom: 0.2rem; }}
.dipc-sidebar a:hover, .dipc-sidebar a.active {{ background: var(--dipc-accent-muted); color: var(--dipc-accent); }}
.dipc-main {{ padding: var(--dipc-space-lg) var(--dipc-space-xl) var(--dipc-space-2xl); }}
.dipc-hero {{ background: linear-gradient(135deg, var(--dipc-bg-surface), var(--dipc-bg-card)); border: 1px solid var(--dipc-border-default); border-left: 4px solid var(--dipc-accent); border-radius: 18px; padding: var(--dipc-space-xl); box-shadow: var(--dipc-shadow); }}
.dipc-section {{ margin-top: var(--dipc-space-xl); background: var(--dipc-bg-surface); border: 1px solid var(--dipc-border-default); border-radius: 18px; padding: var(--dipc-space-lg); box-shadow: var(--dipc-shadow); }}
.dipc-component h3, .dipc-hero h1 {{ font-family: var(--dipc-headline); }}
.dipc-card-grid, .dipc-kpi-grid, .dipc-matrix-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: var(--dipc-space-md); }}
.dipc-card, .dipc-kpi, .dipc-matrix-cell, .dipc-tree-root, .dipc-tree-child, .dipc-svg-card {{ background: var(--dipc-bg-card); border: 1px solid var(--dipc-border-default); border-radius: 14px; padding: var(--dipc-space-md); }}
.dipc-kpi strong {{ display: block; font-size: 2rem; color: var(--dipc-accent); }}
.dipc-table-wrap {{ overflow-x: auto; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ border-bottom: 1px solid var(--dipc-border-default); padding: 0.65rem; text-align: left; }}
.timeline svg, .dipc-component svg {{ width: 100%; height: auto; }}
.timeline circle, .timeline line {{ stroke: var(--dipc-accent); fill: var(--dipc-bg-card); stroke-width: 3; }}
.timeline text {{ fill: var(--dipc-text-primary); font-family: var(--dipc-body); font-size: 14px; }}
.dipc-chevron-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: var(--dipc-space-sm); }}
.dipc-chevron {{ position: relative; background: var(--dipc-bg-card); border: 1px solid var(--dipc-border-default); padding: var(--dipc-space-md); border-radius: 12px; clip-path: polygon(0 0, 92% 0, 100% 50%, 92% 100%, 0 100%, 8% 50%); }}
.dipc-pyramid {{ display: flex; flex-direction: column; align-items: center; gap: 0.35rem; }}
.dipc-pyramid-level {{ text-align: center; background: var(--dipc-bg-card); border: 1px solid var(--dipc-border-default); padding: 0.75rem; clip-path: polygon(50% 0%, 100% 100%, 0% 100%); min-height: 86px; display: flex; flex-direction: column; justify-content: center; }}
.dipc-cycle {{ position: relative; width: 380px; height: 380px; margin: 0 auto; }}
.dipc-cycle-core {{ width: 180px; height: 180px; border-radius: 50%; background: var(--dipc-accent-muted); border: 2px solid var(--dipc-accent); display: flex; align-items: center; justify-content: center; margin: 0 auto; position: relative; top: 100px; text-align: center; padding: 1rem; }}
.dipc-cycle-item {{ position: absolute; left: 50%; top: 50%; width: 120px; margin-left: -60px; text-align: center; background: var(--dipc-bg-card); border: 1px solid var(--dipc-border-default); border-radius: 14px; padding: 0.5rem; transform-origin: center 150px; }}
.dipc-relationship {{ position: relative; min-height: 420px; }}
.dipc-relationship-core {{ position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); width: 180px; height: 180px; border-radius: 50%; background: var(--dipc-accent-muted); border: 2px solid var(--dipc-accent); display: flex; align-items: center; justify-content: center; text-align: center; padding: 1rem; }}
.dipc-relationship-node {{ position: absolute; width: 150px; background: var(--dipc-bg-card); border: 1px solid var(--dipc-border-default); border-radius: 14px; padding: 0.75rem; text-align: center; }}
.dipc-relationship .n1 {{ left: 5%; top: 15%; }} .dipc-relationship .n2 {{ right: 5%; top: 15%; }} .dipc-relationship .n3 {{ left: 10%; bottom: 15%; }} .dipc-relationship .n4 {{ right: 10%; bottom: 15%; }} .dipc-relationship .n5 {{ left: 50%; transform: translateX(-50%); top: 0; }} .dipc-relationship .n6 {{ left: 50%; transform: translateX(-50%); bottom: 0; }}
.dipc-tree-children {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: var(--dipc-space-md); margin-top: var(--dipc-space-md); }}
.dipc-preview-browser {{ background: var(--dipc-bg-surface); border: 1px solid var(--dipc-border-default); border-radius: 16px; padding: var(--dipc-space-md); }}
.dipc-browser-toolbar {{ display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: var(--dipc-space-sm); }}
.dipc-browser-chip {{ border: 1px solid var(--dipc-border-default); border-radius: 999px; padding: 0.3rem 0.7rem; color: var(--dipc-text-secondary); }}
@media (max-width: {tokens['breakpoints']['tablet']}px) {{
  .dipc-shell {{ grid-template-columns: 1fr; }}
  .dipc-sidebar {{ position: static; height: auto; border-right: none; border-bottom: 1px solid var(--dipc-border-default); }}
  .dipc-main {{ padding: var(--dipc-space-md); }}
}}
""".strip()
