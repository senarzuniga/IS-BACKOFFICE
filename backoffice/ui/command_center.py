"""
IS-BACKOFFICE Professional Command Center
Enterprise-grade AI agent interface with natural language commands,
agent orchestration, real-time feedback, and analytics dashboard.
"""

from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from backoffice.ui.components.artwork import render_ingecart_artwork_block

# ─────────────────────────────────────────────────────────────────────────────
# Lazy-import backoffice components so missing env vars don't crash at startup
# ─────────────────────────────────────────────────────────────────────────────
def _load_backoffice():
    try:
        from backoffice.agents.backoffice_agent import backoffice
        return backoffice
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Page config (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
def _configure_page():
    st.set_page_config(
        page_title="IS-BACKOFFICE · Command Center",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────────────────────────────────────
_CSS = """
<style>
/* ── Base ── */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(160deg, #0f172a 0%, #1a2540 100%);
}
[data-testid="stSidebar"] {
    background: #111827;
    border-right: 1px solid #1f2937;
}
/* ── Typography ── */
h1, h2, h3 { color: #f1f5f9 !important; }
p, li, label { color: #cbd5e1; }
/* ── Cards ── */
.cc-metric {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 18px 20px;
    text-align: center;
    margin-bottom: 8px;
}
.cc-metric h2 { font-size: 2rem; margin: 4px 0; color: #f8fafc !important; }
.cc-metric p  { font-size: 0.78rem; color: #94a3b8; margin: 0; }
.cc-metric .label { font-size: 0.85rem; color: #64748b; margin-bottom: 4px; }
/* ── Agent card ── */
.agent-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #1e293b;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.8rem;
    color: #94a3b8;
    border: 1px solid #334155;
    margin: 3px;
}
/* ── Chat bubbles ── */
.bubble-user {
    background: #1e40af;
    border-radius: 12px 12px 2px 12px;
    padding: 10px 14px;
    margin: 6px 0;
    max-width: 80%;
    margin-left: auto;
    color: #f1f5f9;
    font-size: 0.92rem;
}
.bubble-bot {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px 12px 12px 2px;
    padding: 10px 14px;
    margin: 6px 0;
    max-width: 80%;
    color: #e2e8f0;
    font-size: 0.92rem;
}
.bubble-ts {
    font-size: 0.7rem;
    color: #475569;
    margin-top: 4px;
}
/* ── Timeline ── */
.tl-item {
    padding: 8px 12px;
    margin: 4px 0;
    border-left: 3px solid #3b82f6;
    background: #1e293b;
    border-radius: 0 8px 8px 0;
}
/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0f172a; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
/* ── Tab overrides ── */
[data-testid="stTabs"] button { color: #94a3b8 !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color: #60a5fa !important; border-bottom: 2px solid #3b82f6; }
/* ── Status badge ── */
.badge-ok  { color: #4ade80; font-weight: 700; }
.badge-off { color: #f87171; font-weight: 700; }
/* ── Divider ── */
hr { border-color: #1f2937; }
</style>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Agent definitions
# ─────────────────────────────────────────────────────────────────────────────
class AgentType(Enum):
    ADMIN      = "Administration"
    FINANCE    = "Finance & Invoicing"
    DOCUMENT   = "Document Management"
    CALENDAR   = "Calendar & Scheduling"
    EMAIL      = "Email & Communication"
    FORMS      = "Forms & Data Collection"
    REPORTING  = "Reporting & Analytics"
    MASTER     = "Master Orchestrator"


AGENT_META: Dict[AgentType, Dict] = {
    AgentType.ADMIN: {
        "icon": "📋", "color": "#3b82f6",
        "caps": ["Task management", "Workflow approval", "Deadline tracking", "Resource allocation"],
        "examples": [
            "Create a high-priority task to review contracts due next Friday",
            "Show me all my pending tasks",
            "Assign the budget report to the finance team with a 3-day deadline",
        ],
    },
    AgentType.FINANCE: {
        "icon": "💰", "color": "#10b981",
        "caps": ["Invoice generation", "Payment tracking", "Expense management", "Financial reporting"],
        "examples": [
            "Generate invoice for €5,000 to Acme Corp",
            "Show all unpaid invoices older than 30 days",
            "Create monthly financial report for this period",
        ],
    },
    AgentType.DOCUMENT: {
        "icon": "📄", "color": "#f59e0b",
        "caps": ["Document storage", "Smart search", "Auto-tagging", "Template management"],
        "examples": [
            "Find all contracts from January 2026",
            "Store contract.pdf in the Legal folder with tags 'client, signed'",
            "Search for NDA documents",
        ],
    },
    AgentType.CALENDAR: {
        "icon": "📅", "color": "#8b5cf6",
        "caps": ["Event scheduling", "Meeting coordination", "Reminder system", "Agenda optimization"],
        "examples": [
            "Schedule a client meeting tomorrow at 2 PM for 1 hour",
            "Show my schedule for today",
            "Book a 30-min call with the team next Monday at 10 AM",
        ],
    },
    AgentType.EMAIL: {
        "icon": "✉️", "color": "#ec4899",
        "caps": ["Email sending", "Auto-response", "Bulk marketing", "Follow-up reminders"],
        "examples": [
            "Send thank-you email to all clients who paid this month",
            "Draft a follow-up for pending invoices",
            "Check unread emails and flag urgent ones",
        ],
    },
    AgentType.FORMS: {
        "icon": "📝", "color": "#14b8a6",
        "caps": ["Form creation", "Data collection", "Submission tracking", "Survey analysis"],
        "examples": [
            "Create a client feedback form with satisfaction rating",
            "Show all form submissions from last week",
            "Create an expense reimbursement request form",
        ],
    },
    AgentType.REPORTING: {
        "icon": "📊", "color": "#ef4444",
        "caps": ["KPI tracking", "Performance analysis", "Trend detection", "Dashboard creation"],
        "examples": [
            "Generate weekly performance report",
            "Show revenue trends for the last 6 months",
            "Create a pipeline summary dashboard",
        ],
    },
    AgentType.MASTER: {
        "icon": "🎯", "color": "#fbbf24",
        "caps": ["Cross-agent coordination", "Complex workflows", "Intelligent routing", "Auto-optimization"],
        "examples": [
            "Onboard new client TechCorp including contract, invoice setup and calendar",
            "Process invoice payment and update all related records",
            "Prepare quarterly business review with financials and meeting invites",
        ],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Command processor
# ─────────────────────────────────────────────────────────────────────────────
class CommandProcessor:
    """Parse natural language commands and route them to the correct agent."""

    _INTENTS = {
        "create_task":       ["create task", "assign task", "new task", "add task", "todo"],
        "show_tasks":        ["show tasks", "list tasks", "my tasks", "pending tasks", "open tasks"],
        "create_invoice":    ["create invoice", "generate invoice", "new invoice", "invoice for"],
        "show_invoices":     ["show invoices", "list invoices", "pending invoices", "unpaid invoices"],
        "schedule_event":    ["schedule", "create meeting", "book meeting", "calendar event", "set meeting"],
        "show_calendar":     ["show calendar", "my schedule", "today schedule", "upcoming events"],
        "send_email":        ["send email", "email to", "notify", "send a mail"],
        "search_documents":  ["find document", "search for", "look up", "get document", "find file"],
        "create_form":       ["create form", "build form", "new form", "survey"],
        "generate_report":   ["generate report", "create report", "weekly report", "monthly report", "daily report"],
        "onboard_client":    ["onboard", "new client setup", "client onboarding"],
    }

    def parse(self, raw: str) -> Dict[str, Any]:
        lower = raw.lower()
        intent = self._detect_intent(lower)
        params = self._extract_params(raw, lower)
        return {"raw": raw, "intent": intent, "params": params, "ts": datetime.now().isoformat()}

    def _detect_intent(self, text: str) -> str:
        for intent, kws in self._INTENTS.items():
            if any(kw in text for kw in kws):
                return intent
        return "general"

    def _extract_params(self, raw: str, lower: str) -> Dict[str, Any]:
        p: Dict[str, Any] = {}

        # Dates
        if "tomorrow" in lower:
            p["date"] = (datetime.now() + timedelta(days=1)).date().isoformat()
        elif "next week" in lower:
            p["date"] = (datetime.now() + timedelta(days=7)).date().isoformat()
        elif "today" in lower:
            p["date"] = datetime.now().date().isoformat()

        # Priority
        if any(w in lower for w in ["urgent", "high priority", "asap"]):
            p["priority"] = "high"
        elif "low priority" in lower:
            p["priority"] = "low"
        else:
            p["priority"] = "medium"

        # Currency amounts
        m = re.search(r"[€$£](\d[\d,]*(?:\.\d{2})?)", raw)
        if m:
            p["amount"] = float(m.group(1).replace(",", ""))

        # Email
        m = re.search(r"[\w.\-]+@[\w.\-]+\.\w+", raw)
        if m:
            p["email"] = m.group(0)

        # Client name (naive heuristic: word after "client" or "for")
        for trigger in ["client", "for", "to"]:
            idx = lower.find(trigger + " ")
            if idx != -1:
                rest = raw[idx + len(trigger) + 1:].split()[0].strip('",.')
                if rest and rest[0].isupper():
                    p.setdefault("client_name", rest)
                    break

        return p

    def execute(self, raw: str, backoffice_agent, progress: Callable) -> Dict[str, Any]:
        """Synchronous execution — wraps async agents if needed."""
        parsed = self.parse(raw)
        intent = parsed["intent"]
        params = parsed["params"]

        try:
            progress(f"🔍 Detected intent: **{intent.replace('_', ' ').title()}**")

            if backoffice_agent is None:
                progress("⚠️ BackofficeAgent unavailable — running in demo mode")
                result = self._demo_result(intent, params)
                agent_name = "Demo Mode"
            else:
                result, agent_name = self._route(intent, params, raw, backoffice_agent, progress)

            progress(f"✅ Completed by **{agent_name}**")
            return {"ok": True, "agent": agent_name, "intent": intent, "result": result, "parsed": parsed}

        except Exception as exc:
            progress(f"❌ Error: {exc}")
            return {"ok": False, "error": str(exc), "intent": intent, "parsed": parsed}

    def _route(self, intent: str, params: Dict, raw: str, ba, progress: Callable):
        if intent == "create_task":
            progress("📋 Creating task via Administration Agent…")
            r = ba.assign_task(
                title=raw[:120],
                description=raw,
                assignee="isenar.cta@gmail.com",
                priority=params.get("priority", "medium"),
                due_days=1 if "tomorrow" in raw.lower() else 7,
            )
            return r, AgentType.ADMIN.value

        if intent == "show_tasks":
            progress("📋 Fetching tasks via Administration Agent…")
            r = ba.get_my_tasks("isenar.cta@gmail.com")
            return r, AgentType.ADMIN.value

        if intent == "create_invoice":
            progress("💰 Generating invoice via Finance Agent…")
            r = ba.create_invoice(
                client_name=params.get("client_name", "Client"),
                client_email=params.get("email", "client@example.com"),
                items=[{"description": "Services rendered", "quantity": 1,
                        "unit_price": params.get("amount", 1000)}],
                due_days=30,
            )
            return r, AgentType.FINANCE.value

        if intent == "show_invoices":
            progress("💰 Loading invoices via Finance Agent…")
            r = ba.db.get_invoices(status="sent")
            return r, AgentType.FINANCE.value

        if intent == "schedule_event":
            progress("📅 Scheduling event via Calendar Agent…")
            r = ba.schedule_event(
                title=raw[:120],
                description=raw,
                start=datetime.now() + timedelta(days=1),
                duration_hours=1,
                attendees=["isenar.cta@gmail.com"],
            )
            return r, AgentType.CALENDAR.value

        if intent == "show_calendar":
            progress("📅 Loading schedule via Calendar Agent…")
            r = ba.get_today_schedule()
            return r, AgentType.CALENDAR.value

        if intent == "send_email":
            progress("✉️ Sending email via Communication Agent…")
            ok = ba.google.send_email(
                to=params.get("email", "recipient@example.com"),
                subject=raw[:120],
                body=raw,
            )
            return {"sent": ok}, AgentType.EMAIL.value

        if intent == "search_documents":
            progress("📄 Searching documents via Document Agent…")
            r = ba.search_documents(query=raw)
            return r, AgentType.DOCUMENT.value

        if intent == "create_form":
            progress("📝 Creating form via Forms Agent…")
            r = ba.create_form(
                title=raw[:120],
                fields=[{"name": "response", "type": "text", "required": True}],
                submit_to="database",
            )
            return r, AgentType.FORMS.value

        if intent == "generate_report":
            progress("📊 Generating report via Reporting Agent…")
            r = ba.generate_daily_report()
            return {"content": r}, AgentType.REPORTING.value

        if intent == "onboard_client":
            progress("🎯 Running full onboarding via Master Orchestrator…")
            client = params.get("client_name", "New Client")
            t = ba.assign_task(title=f"Onboard {client}", description=raw,
                               assignee="isenar.cta@gmail.com", priority="high", due_days=3)
            c = ba.schedule_event(title=f"Kickoff — {client}", description=raw,
                                  start=datetime.now() + timedelta(days=2),
                                  duration_hours=1, attendees=["isenar.cta@gmail.com"])
            return {"task": t, "calendar": c, "client": client}, AgentType.MASTER.value

        # Fallback: generate daily report
        progress("📊 Routing to Reporting Agent (general query)…")
        r = ba.generate_daily_report()
        return {"content": r}, AgentType.REPORTING.value

    def _demo_result(self, intent: str, params: Dict) -> Any:
        """Return illustrative demo data when BackofficeAgent is unavailable."""
        demos: Dict[str, Any] = {
            "create_task":     {"id": "demo-task-001", "title": "Demo Task", "status": "pending", "priority": params.get("priority", "medium")},
            "show_tasks":      [{"title": "Review Q1 Report", "priority": "high", "status": "pending"}, {"title": "Prepare Deck", "priority": "medium", "status": "in_progress"}],
            "create_invoice":  {"invoice_number": "INV-DEMO-001", "client_name": params.get("client_name", "Demo Client"), "total": params.get("amount", 1000), "due_date": (datetime.now() + timedelta(days=30)).date().isoformat()},
            "show_invoices":   [{"invoice_number": "INV-2026-001", "client_name": "Acme Corp", "total": 5000, "status": "sent"}, {"invoice_number": "INV-2026-002", "client_name": "TechCo", "total": 3200, "status": "sent"}],
            "schedule_event":  {"id": "demo-evt-001", "title": "Demo Meeting", "start": (datetime.now() + timedelta(days=1)).isoformat()},
            "show_calendar":   [{"title": "Client Call", "start_time": "10:00", "location": "Google Meet"}, {"title": "Team Standup", "start_time": "11:00", "location": "Office"}],
            "generate_report": {"content": f"# Daily Report — {datetime.now().strftime('%Y-%m-%d')}\n\n**Tasks Completed:** 8\n\n**Pending Invoices:** 3 — Total: €14,200\n\n**Meetings Today:** 2\n\n*Running in demo mode. Connect Supabase/Google for live data.*"},
            "onboard_client":  {"client": params.get("client_name", "New Client"), "task": "created", "calendar": "scheduled"},
        }
        return demos.get(intent, {"message": "Command acknowledged (demo mode)", "intent": intent})


# ─────────────────────────────────────────────────────────────────────────────
# Main Dashboard class
# ─────────────────────────────────────────────────────────────────────────────
class CommandCenter:
    """Renders the full command-center UI."""

    def __init__(self):
        self.processor = CommandProcessor()
        self._init_state()

    # ── Session state ────────────────────────────────────────────────────────
    def _init_state(self):
        defaults = {
            "conversation": [],
            "last_result": None,
            "quick_command": None,
        }
        for k, v in defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v

    # ── Sidebar ──────────────────────────────────────────────────────────────
    def _sidebar(self):
        with st.sidebar:
            st.markdown("## 🎯 IS-BACKOFFICE")
            st.caption("Professional Command Center")
            st.markdown("---")

            # Agent status
            st.markdown("### 🤖 Agents")
            for atype, meta in AGENT_META.items():
                st.markdown(
                    f"<span class='agent-pill'>{meta['icon']} {atype.value} "
                    f"<span class='badge-ok'>●</span></span>",
                    unsafe_allow_html=True,
                )

            st.markdown("---")
            st.markdown("### ⚡ Quick Actions")

            quick = [
                ("📋 Today's Summary",        "Generate daily report"),
                ("💰 Pending Invoices",        "Show all unpaid invoices"),
                ("📅 Next Meeting",            "Show my schedule for today"),
                ("📊 Weekly Performance",      "Generate weekly performance report"),
            ]
            for label, cmd in quick:
                if st.button(label, width='stretch'):
                    st.session_state.quick_command = cmd

            st.markdown("---")
            st.caption("© 2026 IS-BACKOFFICE · v2.0")

    # ── Command input ─────────────────────────────────────────────────────────
    def _command_tab(self, backoffice_agent):
        st.markdown("#### 💬 Natural Language Command Interface")
        st.caption("Type any instruction naturally. The system will route it to the best agent.")

        # Quick example chips
        cols = st.columns(4)
        examples = [
            ("📋 Create Task",    "Create a high-priority task to review Q1 contracts due Friday"),
            ("💰 Invoice",         "Generate invoice for €5,000 to Acme Corp"),
            ("📅 Schedule",        "Schedule client meeting tomorrow at 2 PM for 1 hour"),
            ("📊 Report",          "Generate daily report"),
        ]
        for i, (lbl, cmd) in enumerate(examples):
            with cols[i]:
                if st.button(lbl, width='stretch', key=f"ex_{i}"):
                    st.session_state.quick_command = cmd

        # Consume quick command
        prefill = st.session_state.pop("quick_command", None) or ""

        command = st.text_area(
            "**Your command:**",
            value=prefill,
            height=90,
            placeholder="e.g. 'Onboard new client TechCorp — contract, invoice setup, kickoff meeting'",
            key="command_area",
        )

        col1, col2 = st.columns([4, 1])
        with col2:
            execute = st.button("🚀 Execute", type="primary", width='stretch')

        if execute and command.strip():
            self._run_command(command.strip(), backoffice_agent)

        # Conversation history
        self._render_conversation()

    def _run_command(self, command: str, backoffice_agent):
        st.session_state.conversation.append({
            "role": "user", "text": command,
            "ts": datetime.now().strftime("%H:%M"),
        })

        status_box = st.empty()
        steps: List[str] = []

        def progress(msg: str):
            steps.append(msg)
            with status_box.container():
                for s in steps:
                    st.markdown(s)

        with st.spinner("Executing…"):
            result = self.processor.execute(command, backoffice_agent, progress)

        status_box.empty()
        st.session_state.last_result = result

        bot_msg = (
            f"✅ **{result['agent']}** completed · intent: `{result['intent']}`"
            if result["ok"]
            else f"❌ Error: {result.get('error', 'unknown')}"
        )
        st.session_state.conversation.append({
            "role": "bot", "text": bot_msg,
            "ts": datetime.now().strftime("%H:%M"),
            "result": result,
        })

        # Render result card
        self._render_result_card(result)

    def _render_result_card(self, result: Dict):
        if not result:
            return

        st.markdown("---")
        if not result["ok"]:
            st.error(f"❌ {result.get('error', 'Execution failed')}")
            return

        intent = result.get("intent", "")
        data = result.get("result")

        if intent == "generate_report" and isinstance(data, dict) and "content" in data:
            with st.expander("📋 Report Output", expanded=True):
                st.markdown(data["content"])
                st.download_button(
                    "📥 Download Markdown",
                    data=data["content"],
                    file_name=f"report_{datetime.now():%Y%m%d_%H%M%S}.md",
                    mime="text/markdown",
                )

        elif intent == "create_invoice" and isinstance(data, dict):
            c1, c2, c3 = st.columns(3)
            c1.metric("Invoice", data.get("invoice_number", "N/A"))
            c2.metric("Total", f"€{float(data.get('total', 0)):,.2f}")
            c3.metric("Due", str(data.get("due_date", "N/A")))

        elif intent in ("show_tasks", "show_invoices") and isinstance(data, list) and data:
            df = pd.DataFrame(data)
            st.dataframe(df, width='stretch', hide_index=True)

        elif intent == "show_calendar" and isinstance(data, list):
            if data:
                for ev in data:
                    st.markdown(
                        f"<div class='tl-item'>📅 <strong>{ev.get('title','Event')}</strong>"
                        f" — {ev.get('start_time', ev.get('start',''))}"
                        f"{'  📍 ' + ev.get('location','') if ev.get('location') else ''}</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No upcoming events found.")

        elif intent == "onboard_client" and isinstance(data, dict):
            st.success(f"✅ Client **{data.get('client', 'New Client')}** onboarded successfully")
            st.json(data)

        elif isinstance(data, dict):
            st.json(data)

        elif isinstance(data, list) and data:
            st.dataframe(pd.DataFrame(data), width='stretch', hide_index=True)

        else:
            if data:
                st.write(data)

        with st.expander("🔍 Command analysis"):
            st.json(result.get("parsed", {}))

    def _render_conversation(self):
        conv = st.session_state.conversation
        if not conv:
            return

        st.markdown("---")
        st.markdown("#### 💬 Session History")
        for msg in conv[-14:]:
            if msg["role"] == "user":
                st.markdown(
                    f"<div class='bubble-user'>{msg['text']}"
                    f"<div class='bubble-ts'>{msg['ts']}</div></div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div class='bubble-bot'>{msg['text']}"
                    f"<div class='bubble-ts'>{msg['ts']}</div></div>",
                    unsafe_allow_html=True,
                )

        if st.button("🗑️ Clear History", key="clear_hist"):
            st.session_state.conversation = []
            st.session_state.last_result = None
            st.rerun()

    # ── Analytics tab ─────────────────────────────────────────────────────────
    def _analytics_tab(self, backoffice_agent):
        st.markdown("#### 📊 Backoffice Analytics Dashboard")

        # KPI row
        c1, c2, c3, c4 = st.columns(4)
        kpis = [
            ("📋 Open Tasks",   "24",    "+3 today",   "#3b82f6"),
            ("💰 Revenue MTD",  "€42.5K","+12%",       "#10b981"),
            ("📄 Documents",    "156",   "+23 this wk","#f59e0b"),
            ("⚡ Automation",   "94%",   "↑ efficiency","#8b5cf6"),
        ]
        for col, (label, val, sub, color) in zip([c1, c2, c3, c4], kpis):
            col.markdown(
                f"<div class='cc-metric'>"
                f"<div class='label' style='color:{color}'>{label}</div>"
                f"<h2 style='color:{color} !important'>{val}</h2>"
                f"<p>{sub}</p></div>",
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # Charts row
        col_l, col_r = st.columns(2)

        with col_l:
            task_df = pd.DataFrame({
                "Week": ["Wk 1", "Wk 2", "Wk 3", "Wk 4"],
                "Completed": [12, 15, 18, 22],
                "Created":   [15, 18, 20, 25],
            })
            fig = px.line(
                task_df, x="Week", y=["Completed", "Created"],
                title="📋 Task Trends", markers=True,
                color_discrete_sequence=["#4ade80", "#60a5fa"],
            )
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)", legend_title_text="")
            st.plotly_chart(fig, width='stretch')

        with col_r:
            rev_df = pd.DataFrame({
                "Category": ["Collected", "Invoiced", "Overdue"],
                "Amount":   [35_000, 12_500, 5_000],
            })
            fig = px.pie(
                rev_df, values="Amount", names="Category",
                title="💰 Revenue Distribution", hole=0.45,
                color_discrete_sequence=["#10b981", "#3b82f6", "#ef4444"],
            )
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, width='stretch')

        # Monthly revenue bar
        months = ["Jan", "Feb", "Mar", "Apr", "May"]
        revenue = [28_000, 33_500, 38_000, 41_000, 42_500]
        fig2 = px.bar(
            x=months, y=revenue,
            title="📈 Monthly Revenue (2026)",
            labels={"x": "Month", "y": "Revenue (€)"},
            color=revenue, color_continuous_scale="teal",
        )
        fig2.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(0,0,0,0)", showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig2, width='stretch')

        # Live data section
        st.markdown("---")
        st.markdown("#### 🔴 Live Data")
        if backoffice_agent:
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🔄 Load Live Tasks"):
                    tasks = backoffice_agent.get_my_tasks("isenar.cta@gmail.com")
                    if tasks:
                        st.dataframe(pd.DataFrame(tasks), width='stretch', hide_index=True)
                    else:
                        st.info("No tasks found.")
            with col_b:
                if st.button("🔄 Load Live Invoices"):
                    invoices = backoffice_agent.db.get_invoices(status="sent")
                    if invoices:
                        st.dataframe(pd.DataFrame(invoices), width='stretch', hide_index=True)
                    else:
                        st.info("No pending invoices.")
        else:
            st.info("Connect Supabase to see live data (set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env)")

    # ── Agents tab ────────────────────────────────────────────────────────────
    def _agents_tab(self):
        st.markdown("#### 🤖 Agent Registry & Capabilities")

        for atype, meta in AGENT_META.items():
            with st.expander(f"{meta['icon']}  **{atype.value}**  — {len(meta['caps'])} capabilities"):
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.markdown(f"**Status:** <span class='badge-ok'>● Active</span>", unsafe_allow_html=True)
                    st.markdown("**Capabilities:**")
                    for cap in meta["caps"]:
                        st.markdown(f"- {cap}")
                with c2:
                    st.markdown("**Example commands:**")
                    for ex in meta["examples"]:
                        st.code(ex, language="")
                    if st.button(f"▶ Try example", key=f"try_{atype.value}"):
                        st.session_state.quick_command = meta["examples"][0]
                        st.rerun()

    # ── Intelligence Ingestion tab ────────────────────────────────────────────
    def _intelligence_tab(self):
        """4-layer multi-agent intelligence ingestion dashboard."""
        st.markdown("#### 🔍 Multi-Agent Intelligence Ingestion System")
        st.caption("Discovery → Extraction → Structuring → Intelligence · 4-layer autonomous pipeline")

        # ── Lazy-load pipeline (no-op when pyyaml absent) ─────────────────────
        pipeline = None
        sources = []
        try:
            from backoffice.ingestion.intelligence.pipeline import build_pipeline
            pipeline = build_pipeline()
            sources = pipeline.planner.sources
        except Exception as _e:
            st.warning(
                f"⚠️ Intelligence pipeline not fully initialised ({_e}). "
                "Install `pyyaml` and ensure `config/sources.yaml` exists.",
                icon="⚠️",
            )

        # ── KPI bar ───────────────────────────────────────────────────────────
        stats = pipeline.get_stats() if pipeline else {}
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Sources", len(sources))
        k2.metric("Jobs Processed", stats.get("jobs_processed", 0))
        k3.metric("Successful Scrapes", stats.get("successful_scrapes", 0))
        k4.metric("Failed", stats.get("failed_scrapes", 0))
        k5.metric("Actions Created", stats.get("actions_created", 0))

        st.markdown("---")

        # ── Source registry ───────────────────────────────────────────────────
        col_left, col_right = st.columns([2, 1])

        with col_left:
            st.markdown("##### 📡 Configured Sources")
            if sources:
                tier_colors = {"tier1": "🔴", "tier2": "🟡", "tier3": "🟢"}
                rows = [
                    {
                        "Tier": tier_colors.get(s.tier.value if hasattr(s.tier, "value") else str(s.tier), "⚪"),
                        "Name": s.name,
                        "URL": s.url[:55] + "…" if len(s.url) > 55 else s.url,
                        "Scraper": s.scraper_type,
                        "Data Type": s.data_type,
                        "Freq (h)": s.scraping_frequency_hours,
                        "Priority": s.priority.value if hasattr(s.priority, "value") else str(s.priority),
                        "Active": "✅" if s.is_active else "❌",
                    }
                    for s in sources
                ]
                st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)
            else:
                st.info("No sources loaded. Check `config/sources.yaml` and install `pyyaml`.")

        with col_right:
            st.markdown("##### ⚡ Actions")

            # Run cycle
            if pipeline and st.button("▶ Run Ingestion Cycle", width='stretch', type="primary"):
                with st.spinner("Running planning + scraping + intelligence cycle…"):
                    try:
                        loop = asyncio.new_event_loop()
                        result_stats = loop.run_until_complete(pipeline.run_cycle_once())
                        loop.close()
                        st.success(f"Cycle complete — {result_stats['successful_scrapes']} scrapes, {result_stats['actions_created']} actions")
                    except Exception as exc:
                        st.error(f"Cycle error: {exc}")

            # Reset stats
            if pipeline and st.button("🔄 Reset Stats", width='stretch'):
                pipeline.reset_stats()
                st.success("Stats reset.")

            # Pipeline API link
            st.markdown("---")
            st.markdown("**API Endpoints**")
            st.code("GET  /intelligence-ingestion/status\nGET  /intelligence-ingestion/sources\nPOST /intelligence-ingestion/run-cycle\nPOST /intelligence-ingestion/scrape-now\nGET  /intelligence-ingestion/stats", language="http")

        st.markdown("---")

        # ── Manual Scrape-Now ─────────────────────────────────────────────────
        st.markdown("##### 🕷️ Scrape Now")
        with st.form("scrape_now_form"):
            sc1, sc2, sc3 = st.columns([3, 1, 1])
            with sc1:
                target_url = st.text_input("URL", placeholder="https://www.fosber.com/products")
            with sc2:
                scraper_type = st.selectbox("Scraper", ["static", "dynamic", "antibot"])
            with sc3:
                data_type = st.selectbox("Data Type", ["product", "news", "price", "specs"])
            submitted = st.form_submit_button("🔍 Scrape & Extract", width='stretch')

        if submitted and target_url:
            with st.spinner(f"Scraping {target_url}…"):
                try:
                    from backoffice.ingestion.intelligence.agents.scraper_agent import ScraperAgent
                    from backoffice.ingestion.intelligence.agents.extractor_agent import ExtractorAgent
                    from backoffice.ingestion.intelligence.agents.normalizer_agent import NormalizerAgent
                    from backoffice.ingestion.intelligence.agents.intelligence_agent import IntelligenceAgent

                    loop = asyncio.new_event_loop()

                    async def _do_scrape():
                        scraper = ScraperAgent()
                        extractor = ExtractorAgent(None)
                        normalizer = NormalizerAgent()
                        intel = IntelligenceAgent(None)
                        r = await scraper.scrape(
                            url=target_url, source_id="manual", source_name="Manual",
                            scraper_type=scraper_type,
                        )
                        if not r.success:
                            return None, r.error_message, []
                        ex = await extractor.extract(r.html_content, "manual", "Manual", target_url, data_type)
                        norm = await normalizer.normalize(ex)
                        outputs = await intel.analyze_record("manual", "Manual", target_url, norm.normalized_content)
                        return norm, None, outputs

                    norm, err, outputs = loop.run_until_complete(_do_scrape())
                    loop.close()

                    if err:
                        st.error(f"Scraping failed: {err}")
                    else:
                        st.success(f"Scraped in {scraper_type} mode · confidence {norm.confidence_score:.0%}")
                        t_ex, t_in = st.tabs(["📦 Extracted Data", "💡 Intelligence Outputs"])
                        with t_ex:
                            st.json(norm.normalized_content)
                        with t_in:
                            for out in outputs:
                                impact_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(out.impact, "⚪")
                                st.markdown(f"{impact_color} **{out.title}**")
                                st.markdown(f"*{out.description}*")
                                st.caption(f"→ {out.suggested_action}")
                                st.divider()
                except Exception as exc:
                    st.error(f"Error: {exc}")

        # ── Architecture diagram ───────────────────────────────────────────────
        with st.expander("📐 Pipeline Architecture"):
            st.markdown("""
```
INTERNET
    │
    ▼
┌──────────────────────────────────────┐
│  LAYER 1 · DISCOVERY (PlannerAgent)  │
│  ▸ sources.yaml  ▸ schedule + events │
│  ▸ priority heap (HIGH → LOW)        │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│  LAYER 2 · EXTRACTION (ScraperAgent) │
│  ▸ StaticScraper  (requests)         │
│  ▸ DynamicScraper (Playwright)       │
│  ▸ AntiBotScraper (UA rotation)      │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│  LAYER 3 · STRUCTURING               │
│  ▸ ExtractorAgent  (LLM / regex)     │
│  ▸ NormalizerAgent (EUR, mm, m/min)  │
│  ▸ ProductMatcher  (SHA-1 dedupe)    │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│  LAYER 4 · INTELLIGENCE              │
│  ▸ IntelligenceAgent (signals)       │
│  ▸ SalesAgent → actions table        │
│  ▸ Shared Supabase ← adaptive-sales  │
└──────────────────────────────────────┘
```
**Sources:** Tier-1 competitors (INGECART, Fosber, BHS, MarquipWardUnited) · Tier-2 (DirectIndustry) · Tier-3 news  
**Shared DB tables:** `intelligence_outputs` · `ingestion_structured_data` · `actions` · `ingestion_raw_html`
""")

    # ── Main render ───────────────────────────────────────────────────────────
    def run(self):
        st.markdown(_CSS, unsafe_allow_html=True)

        backoffice_agent = _load_backoffice()

        self._sidebar()

        st.markdown("# 🎯 IS-BACKOFFICE · Command Center")
        st.caption("*Enterprise-grade AI agent orchestration — powered by natural language*")

        if backoffice_agent is None:
            st.warning(
                "⚠️ **Demo Mode** — BackofficeAgent unavailable. "
                "Set `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and `OPENAI_API_KEY` in a `.env` file for full functionality.",
                icon="⚠️",
            )

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "💬 Command Interface",
            "📊 Analytics",
            "🤖 Agents",
            "🔍 Intelligence Ingestion",
            "🎨 INGECART ARTWORK",
            "🏭 Plant Simulator 2D",
        ])

        with tab1:
            self._command_tab(backoffice_agent)
        with tab2:
            self._analytics_tab(backoffice_agent)
        with tab3:
            self._agents_tab()
        with tab4:
            self._intelligence_tab()
        with tab5:
            st.markdown("#### 🎨 INGECART ARTWORK")
            st.caption("Genera creatividades desde una ruta dinámica de imagen y guarda los outputs en la carpeta de marketing.")
            render_ingecart_artwork_block()
        with tab6:
            st.markdown("#### 🏭 Corrugated Plant Simulator")
            st.caption("Acceso directo al simulador 2D para configuración, visualización y análisis de planta.")
            st.info(
                "Usa este panel para abrir el simulador completo y trabajar en modo cliente con configuración guiada, "
                "canvas 2D en tiempo real y analytics de OEE/cuello de botella.",
                icon="ℹ️",
            )
            st.page_link(
                "pages/plant_simulator.py",
                label="Abrir Simulador 2D",
                icon="🏭",
            )


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
def main():
    _configure_page()
    CommandCenter().run()


if __name__ == "__main__":
    main()
