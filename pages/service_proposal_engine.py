"""Service Proposal Engine (SPE) — Main Streamlit Page.

Navigation: ING_DIGHUB > Commercial > Service Proposal Engine
"""
from __future__ import annotations

import difflib
import json
import re
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional

import streamlit as st

from backoffice.spe.database import SPEDatabase
from backoffice.spe.generator import ProposalHTMLGenerator
from backoffice.spe.mission_manager import SPEMissionManager
from backoffice.spe.models import (
    Proposal,
    ProposalStatus,
    ProposalVersion,
    SERVICE_CATALOG,
    ServiceItem,
)
from backoffice.spe.numbering import ProposalNumbering
from backoffice.spe.annual_offer_factory import build_smart_plant_annual_proposals
from backoffice.spe.word_generator import ProposalWordGenerator
from backoffice.spe.validator import validate_proposal_document

REPO_ROOT = Path(__file__).resolve().parent.parent
SPE_REPORT_DIR = REPO_ROOT / "reports" / "spe"
SPE_SMART_OFFERS_DIR = SPE_REPORT_DIR / "smart_plant_annual_offers"
SPE_KNOWLEDGE_DIR = REPO_ROOT / "knowledge_hub" / "spe"
SPE_KNOWLEDGE_LOG = SPE_KNOWLEDGE_DIR / "template_structure_updates.jsonl"
SPE_TEMPLATE_MEMORY = REPO_ROOT / "enterprise_digital_twin" / "spe_template_memory.json"

_DB = SPEDatabase()
_GEN = ProposalHTMLGenerator()
_NUM = ProposalNumbering(_DB)
_MM = SPEMissionManager(_DB, _GEN)
_WORD_GEN = ProposalWordGenerator()

# ─────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────
_PAGE_CSS = """
<style>
/* ── SPE Module styles (tokens consumed from Design System) ── */
.spe-hero {
  background: linear-gradient(120deg, var(--bg-surface) 0%, var(--bg-card) 100%);
  border: 1px solid var(--border-default);
  border-left: 3px solid var(--accent);
  color: var(--text-primary);
  border-radius: 12px;
  padding: 20px 28px;
  margin-bottom: 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.spe-hero h1 { color: var(--text-primary) !important; margin: 0; font-size: 1.5rem; }
.spe-hero .sub { color: var(--text-secondary); font-size: 0.88rem; margin-top: 4px; }
.spe-hero .badge {
  background: var(--accent-muted);
  color: var(--accent);
  border: 1px solid rgba(255,106,0,0.3);
  border-radius: 20px;
  padding: 3px 12px;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  margin-left: 6px;
}
.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  padding: 16px 20px;
  text-align: center;
}
.stat-card .val { font-size: 1.9rem; font-weight: 800; color: var(--metric-value); line-height: 1; }
.stat-card .lbl { font-size: 0.72rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 1px; margin-top: 6px; }
.proposal-row {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 6px;
  transition: border-color 0.15s;
}
.proposal-row:hover { border-color: var(--accent); }
.proposal-number { font-weight: 800; color: var(--text-primary); font-size: 0.95rem; }
.proposal-customer { color: var(--text-primary); font-size: 0.88rem; }
.ingpro-card {
  background: linear-gradient(135deg, var(--bg-surface), var(--bg-card));
  border: 1px solid var(--border-default);
  border-left: 3px solid var(--accent);
  border-radius: 10px;
  padding: 18px 22px;
  margin: 12px 0;
}
.ingpro-card h4 { color: var(--accent) !important; margin: 0 0 8px; }
</style>
"""


# ─────────────────────────────────────────────────────────────────────
# Session helpers
# ─────────────────────────────────────────────────────────────────────
def _ss(key: str, default=None):
    return st.session_state.get(key, default)


def _set(key: str, val):
    st.session_state[key] = val


def _get_editing() -> Optional[Proposal]:
    return _ss("spe_editing_proposal")


def _save_editing(p: Proposal):
    _set("spe_editing_proposal", p)


def _semantic_signature(html: str) -> dict:
    if not html:
        return {
            "h2_sections": 0,
            "service_cards": 0,
            "has_corporate_header": False,
            "has_official_logo": False,
            "has_kpi_cards": False,
        }
    return {
        "h2_sections": len(re.findall(r"<h2\\b", html, flags=re.IGNORECASE)),
        "service_cards": len(re.findall(r'class="service-card"', html)),
        "has_corporate_header": ("corporate-header" in html) or ('class="hero"' in html),
        "has_official_logo": ("ingeeniering.png" in html) or ("data:image/" in html),
        "has_kpi_cards": ("kpi-row" in html) or ("kpi-card" in html),
    }


def _html_diff_summary(previous_html: str, new_html: str) -> dict:
    if not previous_html:
        return {
            "added_lines": len(new_html.splitlines()),
            "removed_lines": 0,
            "changed": True,
            "sample": ["initial_html_created"],
        }

    prev_lines = previous_html.splitlines()
    new_lines = new_html.splitlines()
    diff = list(difflib.unified_diff(prev_lines, new_lines, lineterm=""))
    added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))
    sample = [line for line in diff if line.startswith("+") or line.startswith("-")][:16]
    return {
        "added_lines": added,
        "removed_lines": removed,
        "changed": bool(diff),
        "sample": sample,
    }


def _append_structure_memory(event: dict) -> None:
    SPE_KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    SPE_KNOWLEDGE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with SPE_KNOWLEDGE_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=True) + "\n")

    SPE_TEMPLATE_MEMORY.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if SPE_TEMPLATE_MEMORY.exists():
        try:
            existing = json.loads(SPE_TEMPLATE_MEMORY.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = []
        except Exception:
            existing = []
    existing.append(event)
    SPE_TEMPLATE_MEMORY.write_text(json.dumps(existing[-80:], ensure_ascii=True, indent=2), encoding="utf-8")


def _save_proposal_version(p: Proposal, new_html: str, author: str, reason: str) -> dict:
    previous_html = p.html_output or (p.versions[-1].html_snapshot if p.versions else "")
    semantic_before = _semantic_signature(previous_html)
    semantic_after = _semantic_signature(new_html)
    html_diff = _html_diff_summary(previous_html, new_html)
    visual_diff = {
        "corporate_header_added": (not semantic_before["has_corporate_header"]) and semantic_after["has_corporate_header"],
        "kpi_cards_removed": semantic_before["has_kpi_cards"] and (not semantic_after["has_kpi_cards"]),
        "official_logo_active": semantic_after["has_official_logo"],
    }
    metadata = {
        "ts": datetime.now().isoformat(),
        "reason": reason,
        "visual_diff": visual_diff,
        "html_diff": html_diff,
        "semantic_diff": {
            "before": semantic_before,
            "after": semantic_after,
        },
    }

    version_num = len(p.versions) + 1
    p.version = max(p.version + 1, version_num)
    p.html_output = new_html
    p.versions.append(
        ProposalVersion(
            version=version_num,
            created_at=datetime.now().isoformat(),
            author=author or "INGECART Engineering",
            changes=json.dumps(metadata, ensure_ascii=True),
            html_snapshot=new_html[:8000],
        )
    )
    p.change_log.append(
        f"[{datetime.now().isoformat()}] v{version_num} snapshot: {reason} | header={semantic_after['has_corporate_header']} | logo={semantic_after['has_official_logo']} | kpi_removed={not semantic_after['has_kpi_cards']}"
    )

    _append_structure_memory(
        {
            "proposal_number": p.number,
            "proposal_id": p.id,
            "version": version_num,
            **metadata,
        }
    )
    return metadata


def _preview_mode_style(mode: str) -> str:
    styles = {
        "Desktop": "html,body{background:#f3f5f7!important;} .page{max-width:1100px!important; box-shadow:0 10px 24px rgba(0,0,0,0.10);}",
        "Tablet": "html,body{background:#e9edf2!important;} .page{max-width:860px!important; padding:16mm 14mm!important; box-shadow:0 10px 24px rgba(0,0,0,0.12);}",
        "Mobile": "html,body{background:#e6ebf2!important;} .page{max-width:420px!important; padding:10mm 8mm!important; font-size:9.8pt!important; box-shadow:0 8px 18px rgba(0,0,0,0.14);} h1{font-size:28px!important;} h2{font-size:14px!important;}",
        "Dark": "html,body{background:#0f131a!important; color:#E8EDF4!important;} .page{background:#121821!important; color:#E8EDF4!important; box-shadow:0 12px 28px rgba(0,0,0,0.45);} .toc,.panel,.service-card,.telemetry-card{background:#1b2430!important; color:#E8EDF4!important;} p,li,td{color:#D8E2EE!important;}",
        "Print": "html,body{background:white!important;} .page{max-width:210mm!important; padding:12mm!important; margin:0 auto!important; box-shadow:none!important;} .no-print{display:none!important;}",
        "PDF": "html,body{background:white!important;} .page{max-width:794px!important; padding:12mm!important; margin:0 auto!important; box-shadow:none!important;} .no-print{display:none!important;} @page{size:A4 portrait; margin:12mm;}",
    }
    return styles.get(mode, styles["Desktop"])


def _apply_preview_mode(html: str, mode: str) -> str:
    injected = f"<style>{_preview_mode_style(mode)}</style>"
    if "</head>" in html:
        return html.replace("</head>", injected + "</head>", 1)
    return injected + html


def _validate_generated_html(html: str) -> dict:
    cover_ix = html.find("<!-- ════ COVER ════ -->")
    toc_ix = html.find("<!-- ════ TOC ════ -->")
    between = html[cover_ix:toc_ix] if cover_ix >= 0 and toc_ix > cover_ix else ""
    has_sidebar_toc = ('class="toc"' in html.lower()) or ("table of contents" in html.lower()) or ("contenido" in html.lower())
    toc_gate = (cover_ix >= 0 and toc_ix > cover_ix and "kpi-" not in between) or has_sidebar_toc
    return {
        "official_logo": ("ingeeniering.png" in html) or ("data:image/" in html),
        "corporate_header": ("corporate-header" in html) or ('class="hero"' in html),
        "kpi_block_removed": ("kpi-row" not in html) and ("kpi-card" not in html),
        "toc_immediately_after_cover": toc_gate,
    }


# ─────────────────────────────────────────────────────────────────────
# Status badge helper
# ─────────────────────────────────────────────────────────────────────
_STATUS_COLORS = {
    "draft":    "var(--text-disabled)",
    "review":   "var(--warning)",
    "sent":     "var(--info)",
    "accepted": "var(--success)",
    "rejected": "var(--error)",
    "expired":  "var(--text-secondary)",
    "archived": "var(--border-strong)",
}


def _status_badge(status: str) -> str:
    color = _STATUS_COLORS.get(status, "#888")
    return f'<span style="background:{color};color:white;border-radius:20px;padding:2px 10px;font-size:0.72rem;font-weight:700;">{status.upper()}</span>'


# ─────────────────────────────────────────────────────────────────────
# CASCADES default template
# ─────────────────────────────────────────────────────────────────────
def _build_cascades_template() -> Proposal:
    """Build the CASCADES PISCATAWAY reference proposal (OFF-2026-S131)."""
    p = Proposal()
    p.title = "Customer Support & Lifecycle Services — Preventive Maintenance Programme"
    p.customer = "CASCADES PISCATAWAY"
    p.plant = "Piscataway Plant"
    p.customer_country = "USA"
    p.language = "en"
    p.currency = "EUR"
    p.responsible = "INGECART Engineering"
    p.duration = "12 months"
    p.validity_days = 45
    p.payment_terms = "50% upon order, 50% upon first visit"
    p.template_id = "SPE-CASCADES-CORPORATE-V2"
    p.change_log.append(
        f"[{datetime.now().isoformat()}] Template upgraded to CorporateHeader V2 and KPI card block removed"
    )

    # Preventive maintenance service
    maint = ServiceItem(
        service_id="preventive_maintenance",
        name="Preventive Maintenance Programme",
        description=(
            "4 scheduled preventive maintenance visits per year, 3 days per visit, "
            "2 INGECART engineers. Each visit includes full mechanical and electrical "
            "inspection, lubrication, calibration, and functional testing. "
            "Detailed technical report after each visit. Annual improvement plan included."
        ),
        price=35000.0,
        unit="year",
        frequency="4 visits / year",
        hours_per_event=24.0,
        persons=2,
        coverage="Full installation — mechanical, electrical, automation",
        objectives=(
            "Maintain equipment availability >95%, identify emerging failures, "
            "document equipment condition trends."
        ),
        deliverables=(
            "Visit report (PDF), corrective action list, spare parts recommendations, "
            "annual performance report, improvement plan."
        ),
        spare_parts="Lubrication materials included. Additional spare parts at cost.",
        emergency_response="Priority response within 48h for contractual emergencies.",
        notes=(
            "Visits can be brought forward at customer request. Scope extension for "
            "component replacement subject to separate approval."
        ),
        enabled=True,
        optional=False,
    )

    # IngPRO as optional
    ingpro = ServiceItem(
        service_id="ingpro",
        name="IngPRO Digital Monitoring",
        description=(
            "Continuous cloud-based condition monitoring via sensor network. "
            "Captures vibration (10+ axes), temperature, electrical consumption and PLC tags. "
            "AI algorithms detect bearing defects, gear faults, misalignment and process anomalies. "
            "Monthly reports and real-time alerts included."
        ),
        price=15000.0,
        unit="year",
        frequency="Continuous 24/7",
        coverage="Key mechanical equipment and drive systems",
        deliverables="Monthly monitoring summary, real-time alert dashboard, annual trend report",
        enabled=True,
        optional=True,
    )

    p.services = [maint, ingpro]

    p.executive_summary = (
        "<p>INGECART is pleased to present this proposal for a 4-visit annual Preventive Maintenance "
        "Programme for the CASCADES PISCATAWAY plant. Based on our engineering assessment of your "
        "installation, we have designed a programme that ensures maximum equipment availability, "
        "minimises unplanned downtime, and protects your capital investment.</p>"
        "<p>The programme includes 4 visits per year (3 days / 2 engineers each), comprehensive "
        "technical reporting, a corrective action plan, and an annual improvement roadmap. "
        "Optional IngPRO digital monitoring is also offered to complement the preventive "
        "programme with continuous predictive surveillance.</p>"
        "<div class='callout'><p><strong>Total Investment:</strong> €35,000 / year (preventive maintenance programme). "
        "Optional IngPRO: +€15,000 / year.</p></div>"
    )

    return p


# ─────────────────────────────────────────────────────────────────────
# Dashboard Tab
# ─────────────────────────────────────────────────────────────────────
def _tab_dashboard():
    stats = _DB.stats()
    by_status = stats.get("by_status", {})

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.markdown(f'<div class="stat-card"><div class="val">{stats["total"]}</div><div class="lbl">Total Proposals</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="stat-card"><div class="val">{by_status.get("draft",0)}</div><div class="lbl">Drafts</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="stat-card"><div class="val">{by_status.get("sent",0)}</div><div class="lbl">Sent</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="stat-card"><div class="val">{by_status.get("accepted",0)}</div><div class="lbl">Accepted</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="stat-card"><div class="val">{stats["next_number"]}</div><div class="lbl">Next Number</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Recent Proposals")

    proposals = _DB.list_all(limit=20)
    if not proposals:
        st.info("No proposals yet. Create your first proposal using the **New Proposal** tab.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ New Blank Proposal", use_container_width=True, type="primary"):
                _set("spe_tab", "new")
                st.rerun()
        with col2:
            if st.button("📋 Load CASCADES Template", use_container_width=True):
                tmpl = _build_cascades_template()
                _save_editing(tmpl)
                _set("spe_tab", "edit")
                st.rerun()
        return

    for p in proposals:
        c_num, c_cust, c_title, c_status, c_date, c_actions = st.columns([1.5, 2, 3, 1.2, 1.5, 2])
        with c_num:
            st.markdown(f"**{p.display_number}**")
        with c_cust:
            st.write(p.customer or "—")
        with c_title:
            st.write(p.title[:60] + "…" if len(p.title) > 60 else p.title or "—")
        with c_status:
            st.markdown(_status_badge(p.status), unsafe_allow_html=True)
        with c_date:
            st.write(p.date_created[:10] if p.date_created else "—")
        with c_actions:
            col_e, col_dup = st.columns(2)
            with col_e:
                if st.button("✏️", key=f"edit_{p.id}", help="Edit"):
                    _save_editing(p)
                    _set("spe_tab", "edit")
                    st.rerun()
            with col_dup:
                if st.button("📋", key=f"dup_{p.id}", help="Duplicate"):
                    dup = _MM.duplicate(p.id)
                    if dup:
                        st.success(f"Duplicated as {dup.number}")
                        st.rerun()


# ─────────────────────────────────────────────────────────────────────
# New Proposal Tab
# ─────────────────────────────────────────────────────────────────────
def _tab_new_proposal():
    st.subheader("➕ New Service Proposal")

    # Quick-load templates
    tmpl_col, _ = st.columns([2, 3])
    with tmpl_col:
        quick = st.selectbox(
            "Load template",
            ["— Blank proposal —", "CASCADES PISCATAWAY (S130 reference)", "Custom…"],
            key="new_template_select",
        )

    if quick == "CASCADES PISCATAWAY (S130 reference)":
        if st.button("Load CASCADES Template", type="primary"):
            _save_editing(_build_cascades_template())
            _set("spe_tab", "edit")
            st.rerun()
        st.markdown("""
> **CASCADES PISCATAWAY** — Reference proposal:
> 4 visits/year · 3 days · 2 engineers · Technical report · Improvement plan
> Possibility to advance visits at customer request.
> Component replacement subject to separate approval.
> **Price: €35,000 / year + Optional IngPRO €15,000 / year**
        """)
        return

    st.markdown("---")
    st.markdown("#### 📋 Basic Information")

    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("Proposal Title *", placeholder="e.g. Preventive Maintenance Programme 2026")
        customer = st.text_input("Customer *", placeholder="e.g. CASCADES PISCATAWAY")
        plant = st.text_input("Plant / Site", placeholder="e.g. Piscataway Plant, NJ")
        customer_country = st.text_input("Country", placeholder="e.g. USA")
        customer_contact = st.text_input("Contact Person")
        customer_email = st.text_input("Contact Email")
    with col2:
        language = st.selectbox("Language", ["en", "es"], format_func=lambda x: "English" if x == "en" else "Español")
        currency = st.selectbox("Currency", ["EUR", "USD"])
        responsible = st.text_input("Responsible (INGECART)", value="INGECART Engineering")
        commercial = st.text_input("Commercial Reference")
        proposal_date = st.date_input("Date", value=date.today())
        validity_days = st.number_input("Validity (days)", value=30, min_value=1)

    col3, col4 = st.columns(2)
    with col3:
        duration = st.text_input("Contract Duration", placeholder="e.g. 12 months")
        payment_terms = st.text_input("Payment Terms", placeholder="e.g. 50% upfront, 50% on delivery")
    with col4:
        incoterm = st.text_input("Incoterm (optional)")
        observations = st.text_area("Observations", height=80)

    st.markdown("---")
    st.markdown("#### ⚙️ Services")
    st.caption("Select and configure the services to include in this proposal.")

    service_configs = {}
    for svc in SERVICE_CATALOG:
        enabled = st.checkbox(f"{svc['icon']} **{svc['name']}**", key=f"new_svc_{svc['id']}")
        if enabled:
            with st.expander(f"Configure: {svc['name']}", expanded=True):
                c1, c2, c3 = st.columns(3)
                price = c1.number_input(f"Price ({currency})", value=float(svc["default_price"]), min_value=0.0, key=f"price_{svc['id']}")
                unit = c2.selectbox("Unit", ["year", "month", "visit", "hour", "lumpsum", "day"], key=f"unit_{svc['id']}")
                optional = c3.checkbox("Optional service", key=f"opt_{svc['id']}")
                c4, c5 = st.columns(2)
                frequency = c4.text_input("Frequency", key=f"freq_{svc['id']}", placeholder="e.g. 4 visits/year")
                hours = c4.number_input("Hours per event", value=0.0, min_value=0.0, key=f"hours_{svc['id']}")
                persons = c5.number_input("Persons", value=1, min_value=1, key=f"pers_{svc['id']}")
                coverage = c5.text_input("Coverage", key=f"cov_{svc['id']}")
                description = st.text_area("Description", value=svc["description"], key=f"desc_{svc['id']}", height=80)
                deliverables = st.text_input("Deliverables", key=f"del_{svc['id']}")
                spare_parts = st.text_input("Spare Parts (scope)", key=f"sp_{svc['id']}")
                emergency = st.text_input("Emergency Response", key=f"em_{svc['id']}")
                notes = st.text_input("Notes", key=f"notes_{svc['id']}")
                service_configs[svc["id"]] = {
                    "service_id": svc["id"],
                    "name": svc["name"],
                    "description": description,
                    "price": price,
                    "unit": unit,
                    "optional": optional,
                    "frequency": frequency,
                    "hours_per_event": hours,
                    "persons": int(persons),
                    "coverage": coverage,
                    "deliverables": deliverables,
                    "spare_parts": spare_parts,
                    "emergency_response": emergency,
                    "notes": notes,
                    "enabled": True,
                }

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("💾 Save as Draft", type="primary", use_container_width=True):
            if not title or not customer:
                st.error("Title and Customer are required.")
            else:
                services = [ServiceItem(**cfg) for cfg in service_configs.values()]
                proposal = Proposal(
                    title=title,
                    customer=customer,
                    plant=plant,
                    customer_country=customer_country,
                    customer_contact=customer_contact,
                    customer_email=customer_email,
                    language=language,
                    currency=currency,
                    responsible=responsible,
                    commercial=commercial,
                    date_created=str(proposal_date),
                    validity_days=validity_days,
                    duration=duration,
                    payment_terms=payment_terms,
                    incoterm=incoterm,
                    observations=observations,
                    services=services,
                    status=ProposalStatus.DRAFT.value,
                    authors=[responsible],
                    change_log=[f"[{datetime.now().isoformat()}] Created by {responsible}"],
                )
                saved = _DB.create(proposal)
                _MM.run_mission(saved, "new_proposal", "Create new proposal from New Proposal tab")
                st.success(f"✅ Proposal {saved.number} saved as draft.")
                _save_editing(saved)
                _set("spe_tab", "edit")
                st.rerun()

    with col_b:
        if st.button("👁️ Preview First (generate)", use_container_width=True):
            if not title:
                st.warning("Enter at least a title to preview.")
            else:
                services = [ServiceItem(**cfg) for cfg in service_configs.values()]
                preview_p = Proposal(
                    id="preview",
                    number=_NUM.preview_next(),
                    title=title, customer=customer, plant=plant, language=language,
                    currency=currency, date_created=datetime.now().isoformat(),
                    services=services, validity_days=validity_days,
                    payment_terms=payment_terms, responsible=responsible,
                )
                html = _GEN.generate(preview_p, preview=True)
                _set("spe_preview_html", html)
                _set("spe_tab", "preview")
                st.rerun()


# ─────────────────────────────────────────────────────────────────────
# Edit / Sections Tab
# ─────────────────────────────────────────────────────────────────────
def _tab_edit():
    p = _get_editing()
    if p is None:
        st.warning("No proposal loaded. Select one from the Dashboard or create a New Proposal.")
        if st.button("← Back to Dashboard"):
            _set("spe_tab", "dashboard")
            st.rerun()
        return

    st.subheader(f"✏️ Editing: {p.display_number} — {p.customer}")

    # Status bar
    col_n, col_s, col_act = st.columns([3, 1.5, 2])
    with col_n:
        st.markdown(f"**{p.title}**")
        st.caption(f"Version {p.version} · Created {p.date_created[:10] if p.date_created else '—'}")
    with col_s:
        new_status = st.selectbox(
            "Status", [s.value for s in ProposalStatus],
            index=[s.value for s in ProposalStatus].index(p.status),
            key="edit_status",
        )
        if new_status != p.status:
            p.status = new_status
    with col_act:
        btn_save, btn_preview, btn_generate, btn_publish, btn_export = st.columns(5)
        with btn_save:
            if st.button("💾 Save", use_container_width=True, type="primary"):
                _DB.update(p, "Manual save")
                _MM.run_mission(p, "save", "Manual save from editor")
                st.success("Saved.")
        with btn_preview:
            if st.button("👁️", use_container_width=True, help="Preview"):
                html = _GEN.generate(p, preview=True)
                _set("spe_preview_html", html)
                _set("spe_tab", "preview")
                st.rerun()
        with btn_generate:
            if st.button("📄 Final", use_container_width=True, help="Generate final HTML"):
                final_html = _GEN.generate(p, preview=False)
                meta = _save_proposal_version(
                    p,
                    final_html,
                    p.responsible or "INGECART Engineering",
                    "Final HTML generated from editor",
                )
                model_path = _GEN.get_model_path(p)
                if model_path:
                    validation = validate_proposal_document(
                        html_text=final_html,
                        model_path=model_path,
                        proposal_language=p.language,
                        proposal_currency=p.currency,
                    )
                    if not validation["ok"]:
                        st.error("Validation failed before publication.")
                        for err in validation["errors"]:
                            st.write(f"- {err}")
                _DB.update(p, "Final HTML generated with structure version snapshot")
                _MM.run_mission(p, "generate_html", "Generate final HTML from editor")
                # Save to file
                SPE_REPORT_DIR.mkdir(parents=True, exist_ok=True)
                out_file = SPE_REPORT_DIR / f"{p.number.replace('/','-')}.html"
                out_file.write_text(p.html_output, encoding="utf-8")
                try:
                    word_dir = SPE_REPORT_DIR / "word"
                    word_path = _WORD_GEN.generate(p, word_dir)
                    p.docx_path = str(word_path)
                    _DB.update(p, "Generated Word proposal")
                except Exception as exc:
                    st.warning(f"Word generation warning: {exc}")
                st.success(f"Final HTML saved: {out_file.name}")
                st.caption(
                    f"Version metadata: +{meta['html_diff']['added_lines']} / -{meta['html_diff']['removed_lines']} lines | "
                    f"logo={meta['visual_diff']['official_logo_active']}"
                )
                st.download_button(
                    "⬇️ Download HTML",
                    data=p.html_output.encode("utf-8"),
                    file_name=f"{p.number}.html",
                    mime="text/html",
                )
        with btn_publish:
            if st.button("✅ Publish", use_container_width=True, help="Run publish gates"):
                try:
                    publish_result = _MM.publish(p)
                    st.success(f"Published: {publish_result.get('publication_state', 'Published')}")
                except Exception as exc:
                    st.error(f"Publish blocked: {exc}")
        with btn_export:
            if st.button("📦 Export", use_container_width=True, help="Export published bundle"):
                try:
                    zip_path = _MM.export_release_bundle(p)
                    st.success(f"Exported bundle: {zip_path}")
                except Exception as exc:
                    st.error(f"Export blocked: {exc}")

    st.markdown("---")

    edit_tabs = st.tabs([
        "📋 Header", "⚙️ Services", "📝 Sections", "🤖 AI Assistant", "📜 History"
    ])

    # ── Header ──
    with edit_tabs[0]:
        c1, c2 = st.columns(2)
        with c1:
            p.title = st.text_input("Title", value=p.title)
            p.customer = st.text_input("Customer", value=p.customer)
            p.plant = st.text_input("Plant", value=p.plant)
            p.customer_contact = st.text_input("Contact", value=p.customer_contact)
            p.customer_email = st.text_input("Email", value=p.customer_email)
            p.customer_country = st.text_input("Country", value=p.customer_country)
        with c2:
            p.language = st.selectbox("Language", ["en", "es"], index=0 if p.language == "en" else 1)
            p.currency = st.selectbox("Currency", ["EUR", "USD"], index=0 if p.currency == "EUR" else 1)
            p.responsible = st.text_input("Responsible", value=p.responsible)
            p.duration = st.text_input("Duration", value=p.duration)
            p.validity_days = st.number_input("Validity (days)", value=int(p.validity_days), min_value=1)
            p.payment_terms = st.text_input("Payment Terms", value=p.payment_terms)
        p.observations = st.text_area("Observations", value=p.observations, height=80)

    # ── Services ──
    with edit_tabs[1]:
        st.markdown("#### Active Services")
        catalog_ids = {s["id"] for s in SERVICE_CATALOG}

        for i, svc in enumerate(p.services):
            with st.expander(f"{'🔴' if not svc.enabled else '🟢'} {svc.name}", expanded=False):
                c1, c2, c3, c4 = st.columns(4)
                svc.enabled = c1.checkbox("Enabled", value=svc.enabled, key=f"en_{i}")
                svc.optional = c2.checkbox("Optional", value=svc.optional, key=f"op_{i}")
                svc.price = c3.number_input("Price", value=float(svc.price), min_value=0.0, key=f"pr_{i}")
                svc.unit = c4.selectbox("Unit", ["year", "month", "visit", "hour", "lumpsum", "day"], key=f"un_{i}")
                svc.frequency = st.text_input("Frequency", value=svc.frequency, key=f"fr_{i}")
                c5, c6 = st.columns(2)
                svc.hours_per_event = c5.number_input("Hours/event", value=float(svc.hours_per_event), min_value=0.0, key=f"hr_{i}")
                svc.persons = c6.number_input("Persons", value=int(svc.persons), min_value=1, key=f"pe_{i}")
                svc.description = st.text_area("Description", value=svc.description, key=f"de_{i}", height=80)
                svc.deliverables = st.text_input("Deliverables", value=svc.deliverables, key=f"dl_{i}")
                svc.coverage = st.text_input("Coverage", value=svc.coverage, key=f"co_{i}")
                svc.notes = st.text_input("Notes", value=svc.notes, key=f"no_{i}")

        st.markdown("#### ➕ Add Service from Catalog")
        available = [s for s in SERVICE_CATALOG if s["id"] not in {sv.service_id for sv in p.services}]
        if available:
            to_add = st.selectbox("Select service", ["— select —"] + [f"{s['icon']} {s['name']}" for s in available], key="add_svc")
            if to_add != "— select —" and st.button("Add Service"):
                idx = [f"{s['icon']} {s['name']}" for s in available].index(to_add)
                s_def = available[idx]
                new_svc = ServiceItem(
                    service_id=s_def["id"],
                    name=s_def["name"],
                    description=s_def["description"],
                    price=float(s_def["default_price"]),
                    unit=s_def["unit"],
                )
                p.services.append(new_svc)
                _DB.update(p, f"Added service: {new_svc.name}")
                st.success(f"Added: {new_svc.name}")
                st.rerun()

    # ── Sections ──
    with edit_tabs[2]:
        st.markdown("#### Document Sections (editable HTML)")
        st.caption("Edit each section. Use HTML or plain text. The changes are saved to the proposal.")

        section_fields = [
            ("executive_summary", "1. Executive Summary"),
            ("about_ingecart", "2. About INGECART"),
            ("understanding_installation", "3. Understanding Your Installation"),
            ("objectives", "4. Objectives"),
            ("scope_of_services", "5. Scope of Services"),
            ("maintenance_programme", "6. Maintenance Programme"),
            ("visit_methodology", "7. Visit Methodology"),
            ("deliverables", "8. Deliverables"),
            ("ingpro_section", "9. IngPRO (leave empty to auto-generate)"),
            ("optional_services", "10. Optional Services"),
            ("customer_responsibilities", "11. Customer Responsibilities"),
            ("commercial_conditions", "12. Commercial Conditions"),
            ("pricing_summary", "13. Pricing Summary (leave empty to auto-generate)"),
            ("why_ingecart", "14. Why INGECART"),
            ("acceptance", "15. Acceptance"),
            ("annexes", "16. Annexes"),
        ]

        for attr, label in section_fields:
            val = getattr(p, attr, "")
            new_val = st.text_area(label, value=val, height=120, key=f"sec_{attr}")
            setattr(p, attr, new_val)

    # ── AI Assistant ──
    with edit_tabs[3]:
        st.markdown("#### 🤖 AI Writing Assistant")
        st.info(
            "The AI Assistant will register a mission in Mission Manager for each request. "
            "Changes are tracked and reversible."
        )

        quick_actions = [
            "Make the executive summary more executive",
            "Add ROI justification to services",
            "Make the language more technical",
            "Shorten all sections by 30%",
            "Add key benefits bullet points",
            "Translate all sections to Spanish",
            "Add ISO and certification references",
            "Expand the IngPRO section with more technical detail",
            "Make the proposal more sales-oriented",
            "Add client-specific context for corrugated plants",
        ]

        col_qa, col_custom = st.columns(2)
        with col_qa:
            quick_sel = st.selectbox("Quick actions", ["— Select —"] + quick_actions, key="ai_quick")
        with col_custom:
            custom_prompt = st.text_area("Custom instruction", height=80, key="ai_custom",
                                          placeholder="e.g. Add a section about safety compliance…")

        prompt = custom_prompt if custom_prompt.strip() else (quick_sel if quick_sel != "— Select —" else "")

        if prompt and st.button("🚀 Apply AI Instruction", type="primary"):
            # Register as mission (no external AI call in local mode)
            mission_entry = {
                "mission_id": str(uuid.uuid4())[:8],
                "prompt": prompt,
                "status": "queued",
                "registered_at": datetime.now().isoformat(),
                "section": "all",
            }
            p.prompt_history.append({"ts": datetime.now().isoformat(), "prompt": prompt, "status": "queued"})
            p.ai_comments.append(
                f"[{datetime.now().strftime('%H:%M')}] AI instruction queued: {prompt}"
            )
            _DB.update(p, f"AI instruction registered: {prompt[:50]}")
            st.success(f"✅ Instruction registered as Mission {mission_entry['mission_id']}. "
                       f"Connect to AI-FACTORY to execute automatically.")

        if p.prompt_history:
            st.markdown("##### Prompt History")
            for ph in reversed(p.prompt_history[-10:]):
                st.markdown(f"- `{ph.get('ts','')[:16]}` — {ph.get('prompt','')[:80]}")

    # ── History ──
    with edit_tabs[4]:
        st.markdown("#### Change Log")
        if p.change_log:
            for entry in reversed(p.change_log[-30:]):
                st.markdown(f"- {entry}")
        else:
            st.info("No changes recorded yet.")

        st.markdown("#### Versions")
        if p.versions:
            for v in reversed(p.versions):
                st.markdown(f"- v{v.version} · {v.created_at[:16]} · {v.author} — {v.changes}")
        else:
            st.info("No versions saved yet.")

        if st.button("📌 Save Version Snapshot"):
            snap = p.html_output or _GEN.generate(p, preview=True)
            _save_proposal_version(
                p,
                snap,
                p.responsible or "INGECART Engineering",
                "Manual snapshot from history tab",
            )
            _DB.update(p, "Version snapshot saved with diffs")
            st.success(f"Version {len(p.versions)} saved.")

    _save_editing(p)


# ─────────────────────────────────────────────────────────────────────
# Proposals Library Tab
# ─────────────────────────────────────────────────────────────────────
def _tab_library():
    st.subheader("📋 Proposals Library")

    col_s, col_f, col_c = st.columns([3, 2, 2])
    with col_s:
        search = st.text_input("🔍 Search", placeholder="Number, customer, title…", key="lib_search")
    with col_f:
        status_filter = st.selectbox("Status", ["All"] + [s.value for s in ProposalStatus], key="lib_status")
    with col_c:
        customer_filter = st.text_input("Customer filter", key="lib_customer")

    proposals = _DB.list_all(
        status=None if status_filter == "All" else status_filter,
        customer=customer_filter or None,
        search=search or None,
        limit=100,
    )

    st.markdown(f"**{len(proposals)} proposals found**")
    st.markdown("---")

    for p in proposals:
        c1, c2, c3, c4, c5, c6 = st.columns([1.5, 2, 3, 1.2, 1.5, 2.5])
        with c1:
            st.markdown(f"**{p.display_number}**")
        with c2:
            st.write(p.customer or "—")
        with c3:
            t = p.title or "—"
            st.write(t[:55] + "…" if len(t) > 55 else t)
        with c4:
            st.markdown(_status_badge(p.status), unsafe_allow_html=True)
        with c5:
            total = p.total_price
            st.write(f"€{total:,.0f}" if total > 0 else "—")
        with c6:
            bc1, bc2, bc3, bc4 = st.columns(4)
            with bc1:
                if st.button("✏️", key=f"lib_edit_{p.id}", help="Edit"):
                    _save_editing(p)
                    _set("spe_tab", "edit")
                    st.rerun()
            with bc2:
                if st.button("👁️", key=f"lib_view_{p.id}", help="Preview"):
                    html = _GEN.generate(p, preview=True)
                    _set("spe_preview_html", html)
                    _set("spe_tab", "preview")
                    st.rerun()
            with bc3:
                if st.button("📋", key=f"lib_dup_{p.id}", help="Duplicate"):
                    dup = _MM.duplicate(p.id)
                    if dup:
                        st.success(f"→ {dup.number}")
                        st.rerun()
            with bc4:
                if st.button("🗑️", key=f"lib_del_{p.id}", help="Delete"):
                    if _DB.delete(p.id):
                        st.warning(f"Deleted {p.display_number}")
                        st.rerun()


# ─────────────────────────────────────────────────────────────────────
# Preview Tab
# ─────────────────────────────────────────────────────────────────────
def _tab_preview():
    st.subheader("👁️ Document Preview")

    p = _get_editing()
    html = _ss("spe_preview_html", "")

    if p and not html:
        if st.button("Generate Preview", type="primary"):
            html = _GEN.generate(p, preview=True)
            _set("spe_preview_html", html)
            st.rerun()
        return

    if not html:
        st.info("No preview available. Edit a proposal and click Preview.")
        return

    col_actions = st.columns(4)
    with col_actions[0]:
        if st.button("🔄 Regenerate"):
            if p:
                html = _GEN.generate(p, preview=True)
                _set("spe_preview_html", html)
                st.rerun()
    with col_actions[1]:
        if st.button("💾 Generate Final"):
            if p:
                final_html = _GEN.generate(p, preview=False)
                _save_proposal_version(
                    p,
                    final_html,
                    p.responsible or "INGECART Engineering",
                    "Final HTML generated from preview tab",
                )
                _DB.update(p, "Final HTML generated with structure version snapshot")
                SPE_REPORT_DIR.mkdir(parents=True, exist_ok=True)
                fname = f"{p.number.replace('/', '-')}.html"
                (SPE_REPORT_DIR / fname).write_text(final_html, encoding="utf-8")
                try:
                    word_dir = SPE_REPORT_DIR / "word"
                    word_path = _WORD_GEN.generate(p, word_dir)
                    p.docx_path = str(word_path)
                    _DB.update(p, "Generated Word proposal from preview")
                except Exception as exc:
                    st.warning(f"Word generation warning: {exc}")
                st.success(f"Saved as {fname}")
    with col_actions[2]:
        if html:
            st.download_button(
                "⬇️ Download HTML",
                data=html.encode("utf-8"),
                file_name=f"{p.number if p else 'proposal'}.html",
                mime="text/html",
            )
            if p and p.docx_path and Path(p.docx_path).exists():
                st.download_button(
                    "⬇️ Download Word",
                    data=Path(p.docx_path).read_bytes(),
                    file_name=Path(p.docx_path).name,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
    with col_actions[3]:
        if st.button("← Back to Edit"):
            _set("spe_tab", "edit")
            st.rerun()

    st.markdown("---")
    mode = st.selectbox(
        "Preview mode",
        ["Desktop", "Tablet", "Mobile", "Dark", "Print", "PDF"],
        key="spe_preview_mode",
    )
    validations = _validate_generated_html(html)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("CorporateHeader", "PASS" if validations["corporate_header"] else "FAIL")
    c2.metric("Official Logo", "PASS" if validations["official_logo"] else "FAIL")
    c3.metric("KPI Block Removed", "PASS" if validations["kpi_block_removed"] else "FAIL")
    c4.metric("TOC After Cover", "PASS" if validations["toc_immediately_after_cover"] else "FAIL")
    rendered_html = _apply_preview_mode(html, mode)
    st.components.v1.html(rendered_html, height=900, scrolling=True)


# ─────────────────────────────────────────────────────────────────────
# Templates Tab
# ─────────────────────────────────────────────────────────────────────
def _tab_templates():
    st.subheader("📚 Proposal Templates")
    st.info("Templates are pre-filled proposals that can be duplicated and adapted for any customer.")

    templates = [
        {
            "name": "CASCADES PISCATAWAY Reference",
            "desc": "4-visit annual programme · 3 days/visit · 2 engineers · €35,000/year",
            "type": "Preventive Maintenance",
            "language": "EN",
        },
        {
            "name": "Standard PM + IngPRO Bundle",
            "desc": "Preventive maintenance + continuous digital monitoring",
            "type": "Bundle",
            "language": "EN",
        },
        {
            "name": "Programa Mantenimiento Preventivo (ES)",
            "desc": "Propuesta estándar PM en español",
            "type": "Preventive Maintenance",
            "language": "ES",
        },
        {
            "name": "Emergency + Remote Support Package",
            "desc": "Emergency on-site + remote assistance hours package",
            "type": "Support",
            "language": "EN",
        },
    ]

    for tmpl in templates:
        c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
        with c1:
            st.markdown(f"**{tmpl['name']}**")
            st.caption(tmpl["desc"])
        with c2:
            st.write(f"🏷️ {tmpl['type']} · {tmpl['language']}")
        with c3:
            if st.button("Load", key=f"tmpl_{tmpl['name'][:20]}", use_container_width=True):
                built = _build_cascades_template()
                _save_editing(built)
                _set("spe_tab", "edit")
                st.rerun()
        with c4:
            st.write("Built-in")
        st.markdown("---")


def _tab_smart_plant_offers():
    st.subheader("🏭 Smart Plant Annual Offers")
    st.info(
        "Genera automáticamente 5 ofertas anuales en formato Ingecart "
        "(HTML estable + Word) para las plantas definidas en Smart Plant Dashboard."
    )
    generated = _ss("spe_smart_offers_generated", [])
    if st.button("⚙️ Generar 5 ofertas anuales", type="primary"):
        SPE_SMART_OFFERS_DIR.mkdir(parents=True, exist_ok=True)
        html_dir = SPE_SMART_OFFERS_DIR / "html"
        word_dir = SPE_SMART_OFFERS_DIR / "word"
        html_dir.mkdir(parents=True, exist_ok=True)
        word_dir.mkdir(parents=True, exist_ok=True)
        proposals = build_smart_plant_annual_proposals()
        generated = []
        for proposal in proposals:
            saved = _DB.create(proposal)
            final_html = _GEN.generate(saved, preview=False)
            html_name = f"{saved.number.replace('/', '-')}.html"
            html_path = html_dir / html_name
            html_path.write_text(final_html, encoding="utf-8")
            word_path = _WORD_GEN.generate(saved, word_dir)
            saved.docx_path = str(word_path)
            _save_proposal_version(
                saved,
                final_html,
                saved.responsible or "INGECART Engineering",
                "Smart Plant annual offer auto-generated",
            )
            _DB.update(saved, "Generated smart plant annual offer bundle")
            generated.append(
                {
                    "number": saved.number,
                    "customer": saved.customer,
                    "plant": saved.plant,
                    "html_path": str(html_path),
                    "docx_path": str(word_path),
                    "total_eur": round(saved.total_price + saved.optional_price, 0),
                }
            )
        _set("spe_smart_offers_generated", generated)
        st.success(f"✅ {len(generated)} ofertas generadas correctamente.")

    if generated:
        st.markdown("### Ofertas generadas")
        st.dataframe(generated, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────
# Main entry
# ─────────────────────────────────────────────────────────────────────
def main() -> None:
    st.set_page_config(
        page_title="Service Proposal Engine | INGECART",
        page_icon="📄",
        layout="wide",
    )
    try:
        from backoffice.theme import inject_theme
        inject_theme()
    except Exception:
        pass
    st.markdown(_PAGE_CSS, unsafe_allow_html=True)

    # Hero
    p_editing = _get_editing()
    editing_badge = f" — {p_editing.display_number}" if p_editing else ""
    st.markdown(
        f"""<div class="spe-hero">
          <div>
            <h1>📄 Service Proposal Engine</h1>
            <div class="sub">INGECART Commercial Module · ING_DIGHUB{editing_badge}</div>
          </div>
          <div>
            <span class="badge">OFF-AAAA-SXXX</span>
            <span class="badge" style="margin-left:8px;">Next: {_NUM.preview_next()}</span>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

    # Tab routing (state-driven)
    tab_keys = ["dashboard", "new", "edit", "preview", "library", "templates", "smart_offers"]
    tab_labels = ["🏠 Dashboard", "➕ New Proposal", "✏️ Edit", "👁️ Preview", "📋 Library", "📚 Templates", "🏭 Smart Offers"]
    current_tab = _ss("spe_tab", "dashboard")
    tab_idx = tab_keys.index(current_tab) if current_tab in tab_keys else 0

    tabs = st.tabs(tab_labels)
    for i, (tab, key) in enumerate(zip(tabs, tab_keys)):
        if i == tab_idx:
            with tab:
                if key == "dashboard":
                    _tab_dashboard()
                elif key == "new":
                    _tab_new_proposal()
                elif key == "edit":
                    _tab_edit()
                elif key == "preview":
                    _tab_preview()
                elif key == "library":
                    _tab_library()
                elif key == "templates":
                    _tab_templates()
                elif key == "smart_offers":
                    _tab_smart_plant_offers()
        else:
            with tab:
                if st.button(f"Open {tab_labels[i]}", key=f"goto_{key}"):
                    _set("spe_tab", key)
                    st.rerun()


if __name__ == "__main__":
    main()
