from __future__ import annotations

from pathlib import Path

import streamlit as st


REPO_ROOT = Path(__file__).resolve().parents[3]
CTA_BRAND_IMAGE = REPO_ROOT / "assets" / "branding" / "cta_adaptive_commercial_system.svg"
CONSULTING_HTML_REPORT = REPO_ROOT / "reports" / "cta_consulting_next_steps.html"
CONSULTING_QUICKSTART = REPO_ROOT / "docs" / "consultoria_funding_quick_start.html"
CONSULTING_OFFER_SNIPPET = REPO_ROOT / "reports" / "templates" / "CTA_Consulting_Offer_Snippet.html"

CTA_BRAND_NAME = "CTA Adaptive Commercial Systems"
CTA_BRAND_TAGLINE = "De estrategia comercial a crecimiento medible"
CTA_BRAND_PILLARS = ("AI-Augmented Sales", "Commercial Intelligence", "Human Execution")


def _read_svg_markup() -> str:
    if CTA_BRAND_IMAGE.exists():
        return CTA_BRAND_IMAGE.read_text(encoding="utf-8")
    return "<div style='padding:24px;color:#fff;'>CTA Adaptive Commercial Systems</div>"


def inject_consulting_brand_styles() -> None:
    st.markdown(
        """
        <style>
        .cta-brand-shell {
            background: linear-gradient(135deg, #0f172a 0%, #111827 48%, #1e293b 100%);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 18px;
            padding: 22px 24px;
            margin-bottom: 18px;
            box-shadow: 0 20px 45px rgba(15, 23, 42, 0.24);
        }
        .cta-brand-kicker {
            display: inline-block;
            padding: 7px 12px;
            border-radius: 999px;
            border: 1px solid rgba(251, 146, 60, 0.35);
            background: rgba(251, 146, 60, 0.12);
            color: #fdba74;
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 12px;
        }
        .cta-brand-title {
            color: #f8fafc;
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.05;
            margin: 0 0 10px;
        }
        .cta-brand-subtitle {
            color: #cbd5e1;
            font-size: 0.98rem;
            line-height: 1.55;
            margin-bottom: 14px;
        }
        .cta-brand-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        .cta-brand-badge {
            background: rgba(148, 163, 184, 0.16);
            color: #e2e8f0;
            border: 1px solid rgba(148, 163, 184, 0.24);
            border-radius: 999px;
            padding: 6px 12px;
            font-size: 0.78rem;
            font-weight: 600;
        }
        .cta-brand-art {
            background: radial-gradient(circle at top, rgba(56, 189, 248, 0.18), rgba(15, 23, 42, 0.1));
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 18px;
            padding: 10px;
        }
        .cta-mini-card {
            background: rgba(15, 23, 42, 0.68);
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 14px;
            padding: 16px 18px;
            margin-bottom: 12px;
        }
        .cta-mini-card h4 {
            color: #f8fafc !important;
            margin: 0 0 6px;
        }
        .cta-mini-card p {
            color: #cbd5e1;
            margin: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_cta_brand_hero(title: str, subtitle: str, context_label: str = "ERP Profesional") -> None:
    inject_consulting_brand_styles()
    left, right = st.columns([1.5, 1], gap="large")
    with left:
        badges = "".join(f"<span class='cta-brand-badge'>{item}</span>" for item in CTA_BRAND_PILLARS)
        st.markdown(
            f"""
            <div class="cta-brand-shell">
              <div class="cta-brand-kicker">{context_label}</div>
              <div class="cta-brand-title">{title}</div>
              <div class="cta-brand-subtitle">{subtitle}</div>
              <div class="cta-brand-badges">{badges}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(f"<div class='cta-brand-art'>{_read_svg_markup()}</div>", unsafe_allow_html=True)

