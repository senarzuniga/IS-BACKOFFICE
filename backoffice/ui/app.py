from __future__ import annotations

import os
import tempfile
import traceback
from datetime import datetime
from typing import Any

import streamlit as st

st.set_page_config(layout="wide", page_title="Virtual Back Office", page_icon="🏢")

from backoffice.ui.components.results import render_main_content
from backoffice.ui.components.sidebar import render_sidebar


def _initialize_state() -> None:
    defaults: dict[str, Any] = {
        "current_section": "",
        "current_action": "",
        "last_result": None,
        "last_payload": {},
        "processing_queue": [],
        "settings": {"theme": "light", "timezone": "UTC", "notifications": True},
        "last_activity": datetime.now().isoformat(timespec="seconds"),
        "memory_usage": 87,
        "status_logs": ["UI initialized"],
        "last_error": None,
        "module_health": {
            "ingestion": True,
            "cleaning": True,
            "extraction": True,
            "graph": True,
            "analytics": True,
            "reporting": True,
        },
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _append_log(message: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state["status_logs"].append(f"[{ts}] {message}")
    st.session_state["last_activity"] = datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Real operation handlers
# ---------------------------------------------------------------------------

def _run_folder_analysis(folder_path: str, output_type: str = "summary") -> dict[str, Any]:
    """Analyse a local folder using the document_analysis pipeline."""
    from document_analysis.folder_reader import FolderReader
    from document_analysis.document_parser import DocumentParser
    from document_analysis.content_extractor import ContentExtractor
    from document_analysis.context_analyzer import ContextAnalyzer
    from document_analysis.output_generator import OutputGenerator
    from document_analysis.models import OutputFormat

    with st.status("Analysing folder...", expanded=True) as status:
        st.write(f"Reading files from {folder_path}…")
        reader = FolderReader(recursive=True)
        files = reader.discover_files(folder_path)
        stats = reader.get_folder_stats(folder_path)
        st.write(f"Found {len(files)} file(s).")

        parser = DocumentParser()
        extractor = ContentExtractor(use_spacy=False)
        docs = []
        for i, file_info in enumerate(files):
            st.write(f"Parsing ({i + 1}/{len(files)}): {file_info['name']}…")
            doc = parser.parse(file_info["path"])
            doc = extractor.enrich(doc)
            docs.append(doc)

        st.write("Running cross-document analysis…")
        analyzer = ContextAnalyzer()
        analysis = analyzer.analyze_folder(docs, folder_path=folder_path, stats=stats)

        st.write("Generating output…")
        generator = OutputGenerator()
        _fmt_map = {
            "summary": OutputFormat.SUMMARY,
            "executive_summary": OutputFormat.EXECUTIVE_SUMMARY,
            "report": OutputFormat.REPORT,
            "list": OutputFormat.LIST,
            "timeline": OutputFormat.TIMELINE,
            "comparison": OutputFormat.COMPARISON,
        }
        fmt = _fmt_map.get(output_type, OutputFormat.SUMMARY)
        output = generator.generate(analysis, fmt)
        status.update(label="Analysis complete!", state="complete")

    return {
        "type": "document_analysis",
        "folder_path": folder_path,
        "file_count": len(files),
        "doc_count": len(docs),
        "output_content": output.content,
        "output_format": output.output_format.value,
        "word_count": output.word_count,
        "themes": analysis.cross_themes,
        "relationships": len(analysis.relationships),
        "timeline_events": len(analysis.timeline),
        "errors": analysis.processing_errors,
        "narrative": analysis.narrative,
    }


def _run_url_analysis(url: str, output_type: str = "summary") -> dict[str, Any]:
    """Fetch a URL, save content to a temp file, and analyse it."""
    import requests
    from document_analysis.document_parser import DocumentParser
    from document_analysis.content_extractor import ContentExtractor
    from document_analysis.context_analyzer import ContextAnalyzer
    from document_analysis.output_generator import OutputGenerator
    from document_analysis.folder_reader import FolderReader
    from document_analysis.models import OutputFormat, FolderStats, DocumentType

    # Validate URL scheme to prevent SSRF
    if not url.lower().startswith(("http://", "https://")):
        raise ValueError(f"Only http:// and https:// URLs are allowed. Got: {url!r}")

    # Block private/loopback addresses (SSRF protection)
    import socket
    import ipaddress
    from urllib.parse import urlparse as _urlparse
    _hostname = _urlparse(url).hostname or ""
    try:
        _ip_str = socket.gethostbyname(_hostname)
        _ip = ipaddress.ip_address(_ip_str)
        if _ip.is_private or _ip.is_loopback or _ip.is_link_local or _ip.is_reserved:
            raise ValueError(f"Requests to private/internal addresses are not allowed: {_ip_str}")
    except (socket.gaierror, ValueError) as _exc:
        if "not allowed" in str(_exc):
            raise

    with st.status("Fetching and analysing URL...", expanded=True) as status:
        st.write(f"Fetching: {url}…")
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Save as HTML, respecting the response encoding
            fname = "page.html"
            fpath = os.path.join(tmpdir, fname)
            with open(fpath, "wb") as f:
                f.write(resp.content)

            st.write("Parsing content…")
            parser = DocumentParser()
            extractor = ContentExtractor(use_spacy=False)
            doc = parser.parse(fpath)
            doc = extractor.enrich(doc)

            st.write("Analysing…")
            stats = FolderStats(
                folder_path=url,
                total_files=1,
                supported_files=1,
                unsupported_files=0,
                total_size_bytes=len(resp.content),
                files_by_type={DocumentType.HTML.value: 1},
            )
            analyzer = ContextAnalyzer()
            analysis = analyzer.analyze_folder([doc], folder_path=url, stats=stats)

            st.write("Generating output…")
            generator = OutputGenerator()
            _fmt_map = {
                "summary": OutputFormat.SUMMARY,
                "executive_summary": OutputFormat.EXECUTIVE_SUMMARY,
                "report": OutputFormat.REPORT,
            }
            fmt = _fmt_map.get(output_type, OutputFormat.SUMMARY)
            output = generator.generate(analysis, fmt)
            status.update(label="URL analysis complete!", state="complete")

    return {
        "type": "url_analysis",
        "url": url,
        "output_content": output.content,
        "output_format": output.output_format.value,
        "word_count": output.word_count,
        "themes": analysis.cross_themes,
        "narrative": analysis.narrative,
    }


def _run_real_operation(section: str, action: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Route section/action to the appropriate real implementation."""

    # --- Folder-based ingestion and extraction ---
    folder_path = (payload.get("folder_path") or "").strip()

    if section in ("📥 INGESTION", "🔍 EXTRACTION") and folder_path:
        if not os.path.isdir(folder_path):
            raise ValueError(f"Folder not found: {folder_path}")
        output_type = "list" if action in ("Watch folder", "Ingest local files") else "report"
        result = _run_folder_analysis(folder_path, output_type=output_type)
        result["section"] = section
        result["action"] = action
        result["status"] = "complete"
        result["completed_at"] = datetime.now().isoformat(timespec="seconds")
        return result

    # --- URL ingestion ---
    url = (payload.get("url") or "").strip()
    if section == "📥 INGESTION" and action == "Ingest from URL" and url:
        result = _run_url_analysis(url, output_type="summary")
        result["section"] = section
        result["action"] = action
        result["status"] = "complete"
        result["completed_at"] = datetime.now().isoformat(timespec="seconds")
        return result

    # --- Uploaded file ingestion ---
    uploaded = payload.get("files")
    if section == "📥 INGESTION" and uploaded:
        files = uploaded if isinstance(uploaded, list) else [uploaded]
        with st.status("Processing uploaded files...", expanded=True) as status:
            from document_analysis.document_parser import DocumentParser
            from document_analysis.content_extractor import ContentExtractor
            from document_analysis.context_analyzer import ContextAnalyzer
            from document_analysis.output_generator import OutputGenerator
            from document_analysis.folder_reader import FolderReader
            from document_analysis.models import OutputFormat, FolderStats

            parser = DocumentParser()
            extractor = ContentExtractor(use_spacy=False)
            docs = []
            with tempfile.TemporaryDirectory() as tmpdir:
                for uploaded_file in files:
                    if uploaded_file is None:
                        continue
                    fpath = os.path.join(tmpdir, uploaded_file.name)
                    with open(fpath, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    st.write(f"Parsing {uploaded_file.name}…")
                    doc = parser.parse(fpath)
                    doc = extractor.enrich(doc)
                    docs.append(doc)

                if not docs:
                    raise ValueError("No valid files uploaded.")

                reader = FolderReader()
                stats = reader.get_folder_stats(tmpdir)
                analyzer = ContextAnalyzer()
                analysis = analyzer.analyze_folder(docs, folder_path="uploaded files", stats=stats)
                generator = OutputGenerator()
                output = generator.generate(analysis, OutputFormat.SUMMARY)
                status.update(label="Done!", state="complete")

        return {
            "type": "document_analysis",
            "folder_path": "uploaded files",
            "file_count": len(docs),
            "doc_count": len(docs),
            "output_content": output.content,
            "output_format": output.output_format.value,
            "word_count": output.word_count,
            "themes": analysis.cross_themes,
            "relationships": len(analysis.relationships),
            "timeline_events": len(analysis.timeline),
            "errors": analysis.processing_errors,
            "narrative": analysis.narrative,
            "section": section,
            "action": action,
            "status": "complete",
            "completed_at": datetime.now().isoformat(timespec="seconds"),
        }

    # --- Fallback: show an informational message for actions that need data setup ---
    with st.status("Processing...", expanded=True) as status:
        st.info(
            f"**{action}** — this action requires data already ingested into the system. "
            "Use **Ingest local files**, **Watch folder**, or **Ingest from URL** first to load data, "
            "then return to this module."
        )
        status.update(label="Ready", state="complete")

    return {
        "section": section,
        "action": action,
        "status": "complete",
        "payload": payload,
        "completed_at": datetime.now().isoformat(timespec="seconds"),
        "message": (
            f"Action '{action}' in module '{section}' requires previously ingested data. "
            "Ingest documents first using the INGESTION module."
        ),
    }


def _render_error_state() -> None:
    error = st.session_state.get("last_error")
    if not error:
        return

    st.error(f"{error['type']}: {error['message']}")
    with st.expander("Stack trace", expanded=False):
        st.code(error["trace"], language="text")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Retry", key="retry_error"):
            st.session_state["last_error"] = None
            st.rerun()
    with c2:
        if st.button("Report bug", key="report_error"):
            _append_log("Bug report requested from UI")
            st.info("Bug report logged to status panel.")


def _handle_quick_action(label: str) -> None:
    if label == "Document Analysis":
        st.switch_page("pages/document_analysis.py")
        return
    if label == "Instruction Panel":
        st.switch_page("pages/instruction_panel.py")
        return

    _QUICK_ACTION_MAP: dict[str, tuple[str, str]] = {
        "Process All New Files": ("📥 INGESTION", "Bulk import"),
        "Today's Dashboard": ("", ""),
        "Ask AI Assistant": ("📊 ANALYTICS", "Natural language query"),
        "Create Summary": ("📑 REPORTING", "Generate report"),
        "Settings": ("📑 REPORTING", "View report history"),
    }

    if label not in _QUICK_ACTION_MAP:
        return

    section, action = _QUICK_ACTION_MAP[label]
    st.session_state["current_section"] = section
    st.session_state["current_action"] = action

    # Set a completed result immediately so render_main_content shows the correct
    # panel on the next render cycle (without requiring a separate "Run" click).
    if section and action:
        st.session_state["last_result"] = {
            "section": section,
            "action": action,
            "status": "complete",
            "payload": {},
            "completed_at": datetime.now().isoformat(timespec="seconds"),
            "message": f"Quick action triggered: {label}. Adjust options and click "
                       "Run Selected Action to re-execute with custom settings.",
        }
    else:
        # Dashboard — reset result to show the default view
        st.session_state["last_result"] = None

    _append_log(f"Quick action: {label}")
    st.rerun()


def _run_selected_action(sidebar_state: dict[str, Any]) -> None:
    section = sidebar_state.get("section", "")
    action = sidebar_state.get("action", "")
    payload = sidebar_state.get("payload", {})

    if not section or not action:
        return

    try:
        result = _run_real_operation(section, action, payload)
        st.session_state["current_section"] = section
        st.session_state["current_action"] = action
        st.session_state["last_payload"] = payload
        st.session_state["last_result"] = result
        st.session_state["processing_queue"].append(
            {
                "section": section,
                "action": action,
                "status": result.get("status", "complete"),
                "time": result.get("completed_at", datetime.now().isoformat(timespec="seconds")),
            }
        )
        st.session_state["last_error"] = None
        _append_log(f"Completed operation: {section} / {action}")
        st.rerun()
    except Exception as exc:  # noqa: BLE001
        st.session_state["last_error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "trace": traceback.format_exc(),
        }
        _append_log(f"Operation failed: {section} / {action} -> {type(exc).__name__}")


def _render_status_bar() -> None:
    st.markdown("---")
    with st.expander("Status Bar", expanded=True):
        queue = st.session_state.get("processing_queue", [])
        st.caption(f"Pending tasks: {len([item for item in queue if item.get('status') != 'complete'])}")
        for line in st.session_state.get("status_logs", [])[-12:]:
            st.write(line)


def main() -> None:
    _initialize_state()

    st.markdown("# Virtual Back Office Human Interface")
    st.write("Hello World")

    sidebar_state = render_sidebar()

    quick_action = sidebar_state.get("quick_action")
    if quick_action:
        _handle_quick_action(quick_action)

    if sidebar_state.get("run_action"):
        _run_selected_action(sidebar_state)

    _render_error_state()

    render_main_content()
    _render_status_bar()


if __name__ == "__main__":
    main()
