"""
INGECART IS-BACKOFFICE — Global CSS Injector
============================================
Single function to inject the full Design System CSS into any Streamlit page.

Usage:
    from backoffice.theme import inject_theme
    inject_theme()   # call after st.set_page_config()
"""
from __future__ import annotations

import streamlit as st
from .design_system import INDUSTRIAL, Theme

# ─────────────────────────────────────────────────────────────────────────────
# Core CSS template using CSS variables
# ─────────────────────────────────────────────────────────────────────────────
_GLOBAL_CSS_TEMPLATE = """
<style>
/* ═══════════════════════════════════════════════════════════════════════════
   INGECART INDUSTRIAL DESIGN SYSTEM — {version}
   Applied to: IS-BACKOFFICE Streamlit Application
   DO NOT override these styles with hardcoded values. Use CSS variables.
   ═══════════════════════════════════════════════════════════════════════════ */

/* ── CSS Custom Properties (Design Tokens) ─────────────────────────────── */
:root {{
  --bg-primary:    {bg_primary};
  --bg-surface:    {bg_surface};
  --bg-card:       {bg_card};
  --bg-sidebar:    {bg_sidebar};
  --bg-elevated:   {bg_elevated};
  --bg-input:      {bg_input};
  --bg-table-row:  {bg_table_row};

  --border-subtle:  {border_subtle};
  --border-default: {border_default};
  --border-strong:  {border_strong};
  --border-focus:   {border_focus};

  --text-primary:   {text_primary};
  --text-secondary: {text_secondary};
  --text-disabled:  {text_disabled};
  --text-inverse:   {text_inverse};

  --accent:         {accent};
  --accent-hover:   {accent_hover};
  --accent-dark:    {accent_dark};
  --accent-muted:   {accent_muted};

  --success:        {success};
  --success-muted:  {success_muted};
  --warning:        {warning};
  --warning-muted:  {warning_muted};
  --error:          {error};
  --error-muted:    {error_muted};
  --info:           {info};
  --info-muted:     {info_muted};

  --link:           {link};
  --shadow:         {shadow};
  --metric-value:   {metric_value};
  --chart-grid:     {chart_grid};

  --btn-primary-bg:     {btn_primary_bg};
  --btn-primary-text:   {btn_primary_text};
  --btn-secondary-bg:   {btn_secondary_bg};
  --btn-secondary-text: {btn_secondary_text};
}}

/* ── App Container ─────────────────────────────────────────────────────── */
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
.main,
section.main {{
  background: var(--bg-primary) !important;
  color: var(--text-primary) !important;
}}

[data-testid="block-container"],
[data-testid="stVerticalBlock"] {{
  background: transparent !important;
}}

/* ── Sidebar ────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div {{
  background: var(--bg-sidebar) !important;
  border-right: 1px solid var(--border-subtle) !important;
}}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown li,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span {{
  color: var(--text-secondary) !important;
}}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {{
  color: var(--text-primary) !important;
}}
[data-testid="stSidebarNav"] a {{
  color: var(--text-secondary) !important;
  border-radius: 6px !important;
}}
[data-testid="stSidebarNav"] a:hover,
[data-testid="stSidebarNav"] a[aria-current="page"] {{
  background: var(--accent-muted) !important;
  color: var(--accent) !important;
}}

/* ── Typography ─────────────────────────────────────────────────────────── */
h1, h2, h3, h4, h5 {{
  color: var(--text-primary) !important;
  font-weight: 700 !important;
}}
p, li {{
  color: var(--text-primary) !important;
}}
.stMarkdown p {{ color: var(--text-primary) !important; }}
.stCaption, small, figcaption {{
  color: var(--text-secondary) !important;
}}
code, pre {{
  background: var(--bg-surface) !important;
  color: var(--accent) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: 4px !important;
}}

/* ── Metrics ────────────────────────────────────────────────────────────── */
[data-testid="stMetric"] {{
  background: var(--bg-card) !important;
  border: 1px solid var(--border-subtle) !important;
  border-radius: 10px !important;
  padding: 14px 16px !important;
}}
[data-testid="stMetricLabel"] {{
  color: var(--text-secondary) !important;
  font-size: 11px !important;
  letter-spacing: 0.8px !important;
  text-transform: uppercase !important;
}}
[data-testid="stMetricValue"] {{
  color: var(--metric-value) !important;
  font-size: 1.8rem !important;
  font-weight: 800 !important;
  line-height: 1.1 !important;
}}
[data-testid="stMetricDelta"] {{ font-size: 11px !important; }}

/* ── Buttons ────────────────────────────────────────────────────────────── */
.stButton > button {{
  background: var(--bg-card) !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: 6px !important;
  font-weight: 600 !important;
  transition: all 0.15s ease !important;
}}
.stButton > button:hover {{
  border-color: var(--accent) !important;
  color: var(--accent) !important;
  background: var(--accent-muted) !important;
}}
.stButton > button[kind="primary"],
button[data-testid="baseButton-primary"] {{
  background: var(--btn-primary-bg) !important;
  color: var(--btn-primary-text) !important;
  border-color: var(--btn-primary-bg) !important;
}}
.stButton > button[kind="primary"]:hover,
button[data-testid="baseButton-primary"]:hover {{
  background: var(--accent-hover) !important;
  border-color: var(--accent-hover) !important;
  color: var(--btn-primary-text) !important;
}}

/* ── Inputs & Forms ─────────────────────────────────────────────────────── */
input[type="text"], input[type="number"], input[type="email"],
input[type="password"], textarea, select,
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea {{
  background: var(--bg-input) !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: 6px !important;
}}
input::placeholder, textarea::placeholder {{
  color: var(--text-disabled) !important;
}}
[data-baseweb="input"]:focus-within,
[data-baseweb="textarea"]:focus-within {{
  border-color: var(--border-focus) !important;
  box-shadow: 0 0 0 2px var(--accent-muted) !important;
}}
label,
[data-testid="stWidgetLabel"] {{
  color: var(--text-secondary) !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  letter-spacing: 0.5px !important;
}}

/* ── Select boxes ───────────────────────────────────────────────────────── */
[data-baseweb="select"] [data-baseweb="popover"],
[data-baseweb="select"] li,
[data-baseweb="select"] ul {{
  background: var(--bg-elevated) !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--border-default) !important;
}}
[data-baseweb="select"] li:hover {{
  background: var(--accent-muted) !important;
  color: var(--accent) !important;
}}

/* ── Checkboxes & Radio ─────────────────────────────────────────────────── */
[data-testid="stCheckbox"] label,
[data-testid="stRadio"] label {{
  color: var(--text-primary) !important;
}}

/* ── Tabs ────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
  background: var(--bg-surface) !important;
  border-bottom: 1px solid var(--border-subtle) !important;
  border-radius: 8px 8px 0 0 !important;
  gap: 0 !important;
  padding: 0 !important;
}}
.stTabs [data-baseweb="tab"] {{
  background: transparent !important;
  color: var(--text-secondary) !important;
  font-weight: 600 !important;
  font-size: 12px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.8px !important;
  padding: 12px 18px !important;
  border-bottom: 2px solid transparent !important;
  transition: color 0.15s !important;
}}
.stTabs [data-baseweb="tab"]:hover {{
  color: var(--text-primary) !important;
  background: var(--accent-muted) !important;
}}
.stTabs [aria-selected="true"] {{
  background: transparent !important;
  color: var(--accent) !important;
  border-bottom: 2px solid var(--accent) !important;
}}
[data-testid="stTabContent"] {{
  background: var(--bg-surface) !important;
  border: 1px solid var(--border-subtle) !important;
  border-top: none !important;
  padding: 16px !important;
  border-radius: 0 0 8px 8px !important;
}}

/* ── DataFrames / Tables ─────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {{
  border: 1px solid var(--border-subtle) !important;
  border-radius: 8px !important;
  overflow: hidden !important;
}}
[data-testid="stDataFrame"] thead,
[data-testid="stDataFrame"] [data-testid="column-header"] {{
  background: var(--bg-surface) !important;
  color: var(--text-secondary) !important;
  font-size: 11px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.8px !important;
  font-weight: 700 !important;
  border-bottom: 1px solid var(--border-default) !important;
}}
[data-testid="stDataFrame"] [data-testid="cell"] {{
  color: var(--text-primary) !important;
  background: var(--bg-primary) !important;
  border-color: var(--border-subtle) !important;
}}
[data-testid="stDataFrame"] [data-testid="row"]:nth-child(even) [data-testid="cell"] {{
  background: var(--bg-table-row) !important;
}}

/* ── Expander ────────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {{
  border: 1px solid var(--border-subtle) !important;
  border-radius: 8px !important;
  background: var(--bg-surface) !important;
}}
[data-testid="stExpander"] summary {{
  color: var(--text-primary) !important;
  font-weight: 600 !important;
}}
[data-testid="stExpander"] summary:hover {{
  color: var(--accent) !important;
}}

/* ── Info / Warning / Success / Error boxes ─────────────────────────────── */
[data-testid="stAlert"] {{
  border-radius: 8px !important;
  border-width: 1px !important;
  font-size: 13px !important;
}}
[data-testid="stAlert"][kind="info"] {{
  background: var(--info-muted) !important;
  border-color: var(--info) !important;
  color: var(--text-primary) !important;
}}
[data-testid="stAlert"][kind="success"],
.st-success {{
  background: var(--success-muted) !important;
  border-color: var(--success) !important;
  color: var(--text-primary) !important;
}}
[data-testid="stAlert"][kind="warning"],
.st-warning {{
  background: var(--warning-muted) !important;
  border-color: var(--warning) !important;
  color: var(--text-primary) !important;
}}
[data-testid="stAlert"][kind="error"],
.st-error {{
  background: var(--error-muted) !important;
  border-color: var(--error) !important;
  color: var(--text-primary) !important;
}}

/* ── Selectbox popover ───────────────────────────────────────────────────── */
[data-baseweb="popover"] {{
  background: var(--bg-elevated) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: 8px !important;
  box-shadow: 0 8px 24px var(--shadow) !important;
}}

/* ── Progress bar ───────────────────────────────────────────────────────── */
[data-testid="stProgress"] > div > div {{
  background: var(--accent) !important;
}}
[data-testid="stProgress"] > div {{
  background: var(--bg-surface) !important;
  border-radius: 4px !important;
}}

/* ── Spinner ────────────────────────────────────────────────────────────── */
[data-testid="stSpinner"] {{ color: var(--accent) !important; }}

/* ── Divider ────────────────────────────────────────────────────────────── */
hr {{ border-color: var(--border-subtle) !important; }}

/* ── Scrollbar ──────────────────────────────────────────────────────────── */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: var(--bg-primary); }}
::-webkit-scrollbar-thumb {{
  background: var(--border-default);
  border-radius: 4px;
}}
::-webkit-scrollbar-thumb:hover {{ background: var(--border-strong); }}

/* ── Reusable component classes ─────────────────────────────────────────── */
.inge-card {{
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  padding: 16px 20px;
}}
.inge-card:hover {{
  border-color: var(--accent);
}}
.inge-hero {{
  background: linear-gradient(120deg, var(--bg-surface) 0%, var(--bg-card) 100%);
  border: 1px solid var(--border-default);
  border-left: 3px solid var(--accent);
  border-radius: 12px;
  padding: 18px 24px;
  margin-bottom: 16px;
}}
.inge-badge {{
  display: inline-block;
  background: var(--accent-muted);
  color: var(--accent);
  border: 1px solid rgba(255,106,0,0.3);
  border-radius: 20px;
  padding: 2px 10px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.8px;
  text-transform: uppercase;
}}
.inge-metric {{
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  padding: 14px 16px;
  text-align: center;
}}
.inge-metric .val {{
  font-size: 1.9rem;
  font-weight: 800;
  color: var(--metric-value);
  line-height: 1;
}}
.inge-metric .lbl {{
  font-size: 10px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-top: 6px;
}}
.inge-section-title {{
  font-size: 13px;
  font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 1.2px;
  border-bottom: 1px solid var(--border-subtle);
  padding-bottom: 8px;
  margin-bottom: 12px;
}}
.inge-accent {{ color: var(--accent) !important; }}
.inge-muted  {{ color: var(--text-secondary) !important; }}
.inge-success {{ color: var(--success) !important; }}
.inge-warning {{ color: var(--warning) !important; }}
.inge-error   {{ color: var(--error) !important; }}
.inge-tag {{
  display: inline-block;
  background: var(--bg-surface);
  color: var(--text-secondary);
  border: 1px solid var(--border-default);
  border-radius: 4px;
  padding: 1px 8px;
  font-size: 11px;
  margin: 2px;
}}

/* ── Override bright page backgrounds ───────────────────────────────────── */
/* These remove the conflicting light-theme backgrounds set by individual pages */
[data-testid="stApp"] .element-container {{
  background: transparent !important;
}}
</style>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Pre-built CSS string for the INDUSTRIAL theme
# ─────────────────────────────────────────────────────────────────────────────
INDUSTRIAL_CSS = _GLOBAL_CSS_TEMPLATE.format(
    version="v1.0 INDUSTRIAL",
    **{k: getattr(INDUSTRIAL, k) for k in INDUSTRIAL.__dataclass_fields__},  # type: ignore[attr-defined]
)


def get_theme_css(theme: Theme = INDUSTRIAL, version: str = "v1.0") -> str:
    """Return the full CSS string for a given theme."""
    return _GLOBAL_CSS_TEMPLATE.format(
        version=f"{version} {theme.__class__.__name__}",
        **{k: getattr(theme, k) for k in theme.__dataclass_fields__},  # type: ignore[attr-defined]
    )


def inject_theme(theme: Theme = INDUSTRIAL) -> None:
    """
    Inject the Design System CSS into the current Streamlit page.
    Call once per page, after st.set_page_config().
    
    Example:
        st.set_page_config(...)
        from backoffice.theme import inject_theme
        inject_theme()
    """
    css = get_theme_css(theme)
    st.markdown(css, unsafe_allow_html=True)
