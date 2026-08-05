from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import streamlit as st

from backoffice.ing_dighub_platform import MODULE_SPECS


REPO_ROOT = Path(__file__).resolve().parent.parent
TWIN_ROOT = REPO_ROOT / "enterprise_digital_twin"


def _implemented_objects() -> list[str]:
    if not TWIN_ROOT.exists():
        return []
    return sorted([p.name for p in TWIN_ROOT.glob("*.py")] + [p.name for p in TWIN_ROOT.glob("*.json")])


def main() -> None:
    st.set_page_config(page_title="Enterprise Digital Twin", page_icon="🧭", layout="wide")

    try:
        from backoffice.theme import inject_theme
        inject_theme()
    except Exception:
        pass

    st.markdown(
        """
        <style>
          .panel {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            padding: 14px;
            margin-bottom: 10px;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("🧭 Enterprise Digital Twin")
    st.caption("Architecture-aware placeholder with real module and object visibility")

    implemented = _implemented_objects()
    maturity = "M2 - Operational Foundation" if implemented else "M0 - Planned"

    col1, col2 = st.columns([1.5, 1])
    with col1:
        st.markdown("<div class='panel'><h3>Architecture Roadmap</h3></div>", unsafe_allow_html=True)
        st.write(
            [
                "M0: Discovery and capability inventory",
                "M1: Digital object modeling and relation graph",
                "M2: Mission-linked twin observability",
                "M3: Real-time simulator + mission orchestration convergence",
                "M4: Closed-loop optimization with coordinator governance",
            ]
        )

        st.markdown("<div class='panel'><h3>Connected Modules</h3></div>", unsafe_allow_html=True)
        st.dataframe(
            [{"module": m.name, "service": m.service, "description": m.description} for m in MODULE_SPECS],
            use_container_width=True,
        )

    with col2:
        st.markdown("<div class='panel'><h3>Current Maturity</h3></div>", unsafe_allow_html=True)
        st.metric("Maturity", maturity)
        st.metric("Implemented Objects", len(implemented))
        st.metric("Pending Integrations", 4)

        st.markdown("<div class='panel'><h3>Pending Integrations</h3></div>", unsafe_allow_html=True)
        st.write(
            [
                "Live plant telemetry adapters",
                "Cross-link with mission queue runtime",
                "Unified object IDs with platform registry",
                "AI-FACTORY event stream connector",
            ]
        )

    st.markdown("### Objects Already Implemented")
    if implemented:
        st.dataframe(
            [
                {
                    "object": name,
                    "source": f"enterprise_digital_twin/{name}",
                    "last_seen": datetime.fromtimestamp((TWIN_ROOT / name).stat().st_mtime, tz=UTC).isoformat(),
                }
                for name in implemented
            ],
            use_container_width=True,
        )
    else:
        st.info("No twin objects detected yet.")


if __name__ == "__main__":
    main()
