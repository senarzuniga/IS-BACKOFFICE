from __future__ import annotations

from collections import Counter
from typing import Any

from .hypothesis_engine import resolve_uncertainty
from .models import Hypothesis, PresentationAnalysis


def build_theme_tokens(analysis: PresentationAnalysis) -> dict[str, Any]:
    palette = list(analysis.global_palette)

    if not palette:
        decision = resolve_uncertainty(
            "Missing color palette",
            [
                Hypothesis("H1", "Infer palette from industrial defaults", 8.8, 8.0, 9.0, 8.5, "Use INGECART-inspired defaults."),
                Hypothesis("H2", "Use browser defaults", 5.0, 3.5, 10.0, 9.0, "Fast but weak corporate identity."),
            ],
        )
        _ = decision
        palette = ["#0B3D6E", "#E85C1A", "#1A2B3C", "#F4F7FA", "#D0D8E0"]

    font_counter = Counter()
    size_counter = Counter()
    for slide in analysis.slides:
        for element in slide.elements:
            if element.style.font_name:
                font_counter[element.style.font_name] += 1
            if element.style.font_size_pt:
                size_counter[round(element.style.font_size_pt, 1)] += 1

    font_family = font_counter.most_common(1)[0][0] if font_counter else "Segoe UI"
    base_size = size_counter.most_common(1)[0][0] if size_counter else 16.0

    return {
        "colors": {
            "primary": palette[0] if len(palette) > 0 else "#0B3D6E",
            "accent": palette[1] if len(palette) > 1 else "#E85C1A",
            "text": palette[2] if len(palette) > 2 else "#1A2B3C",
            "surface": palette[3] if len(palette) > 3 else "#F4F7FA",
            "border": palette[4] if len(palette) > 4 else "#D0D8E0",
            "palette": palette,
        },
        "typography": {
            "font_family": font_family,
            "base_size_pt": base_size,
        },
        "spacing": {
            "xs": "0.25rem",
            "sm": "0.5rem",
            "md": "1rem",
            "lg": "1.5rem",
            "xl": "2.5rem",
        },
        "radius": {
            "sm": "6px",
            "md": "10px",
            "lg": "16px",
        },
    }


def build_corporate_css(theme: dict[str, Any]) -> str:
    colors = theme["colors"]
    typo = theme["typography"]
    return f"""
:root {{
  --pie-color-primary: {colors['primary']};
  --pie-color-accent: {colors['accent']};
  --pie-color-text: {colors['text']};
  --pie-color-surface: {colors['surface']};
  --pie-color-border: {colors['border']};
  --pie-font-family: '{typo['font_family']}', 'Segoe UI', Arial, sans-serif;
  --pie-base-size: {typo['base_size_pt']}pt;
  --pie-shadow: 0 14px 30px rgba(10, 25, 45, 0.12);
}}

:root[data-theme='dark'] {{
  --pie-color-primary: #8fb8e8;
  --pie-color-accent: #ff9b64;
  --pie-color-text: #edf2f8;
  --pie-color-surface: #0f1720;
  --pie-color-border: #2a3a4f;
}}

* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
  margin: 0;
  font-family: var(--pie-font-family);
  color: var(--pie-color-text);
  background:
    radial-gradient(circle at 85% 15%, rgba(232,92,26,0.12), transparent 30%),
    radial-gradient(circle at 20% 30%, rgba(11,61,110,0.14), transparent 35%),
    linear-gradient(180deg, #f7fbff 0%, #edf3f9 100%);
}}
:root[data-theme='dark'] body {{
  background:
    radial-gradient(circle at 85% 15%, rgba(255,155,100,0.18), transparent 35%),
    radial-gradient(circle at 20% 30%, rgba(143,184,232,0.18), transparent 40%),
    linear-gradient(180deg, #0a1118 0%, #0f1720 100%);
}}
main {{ margin-left: 300px; padding: 1rem 2rem 4rem; }}
@media (max-width: 980px) {{ main {{ margin-left: 0; padding: 0.75rem; }} }}
""".strip()
