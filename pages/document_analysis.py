"""Document Analysis â€” full Streamlit page.

Entry point: pages/document_analysis.py (Streamlit multipage)
"""

from __future__ import annotations

import sys
import os
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Any

import streamlit as st

st.set_page_config(
    page_title="Document Analysis â€” Virtual Back Office",
    page_icon="ðŸ“‚",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Ensure project root is importable
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ---------------------------------------------------------------------------
# Session-state helpers
# ---------------------------------------------------------------------------

_STATE_DEFAULTS: dict[str, Any] = {
    "da_folder_path": "",
    "da_recursive": True,
    "da_max_file_mb": 50.0,
    "da_use_cache": True,
    "da_use_ai": False,
    "da_discovered_files": [],
    "da_folder_stats": None,
    "da_analysis": None,
    "da_output": None,
    "da_output_format": "summary",
    "da_processing": False,
    "da_progress_log": [],
    "da_selected_files": [],
    "da_error": None,
}


def _init_state() -> None:
    for key, val in _STATE_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state["da_progress_log"].append(f"[{ts}] {msg}")


# ---------------------------------------------------------------------------
# Back-button (navigation to main app)
# ---------------------------------------------------------------------------

def _render_back_button() -> None:
    if st.button("â† Back to Main App", key="da_back"):
        st.switch_page("streamlit_app.py")


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def _render_sidebar() -> None:
    with st.sidebar:
        st.title("ðŸ“‚ Document Analysis")
        st.markdown("---")

        # --- Folder selector ---
        st.subheader("1. Select Folder")
        folder_input = st.text_input(
            "Folder path",
            value=st.session_state["da_folder_path"],
            placeholder="C:/Users/you/Documents/project",
            help="Enter the full path to the folder you want to analyse.",
            key="da_folder_input",
        )
        if folder_input != st.session_state["da_folder_path"]:
            st.session_state["da_folder_path"] = folder_input
            st.session_state["da_discovered_files"] = []
            st.session_state["da_folder_stats"] = None
            st.session_state["da_analysis"] = None

        # --- Options ---
        st.subheader("2. Options")
        st.session_state["da_recursive"] = st.checkbox(
            "Include sub-folders", value=st.session_state["da_recursive"]
        )
        st.session_state["da_max_file_mb"] = st.slider(
            "Max file size (MB)", min_value=1, max_value=200, value=int(st.session_state["da_max_file_mb"])
        )
        st.session_state["da_use_cache"] = st.checkbox(
            "Use processing cache", value=st.session_state["da_use_cache"]
        )
        st.session_state["da_use_ai"] = st.checkbox(
            "AI enhancement (requires OPENAI_API_KEY)",
            value=st.session_state["da_use_ai"],
        )

        # --- Discover ---
        st.subheader("3. Discover Files")
        if st.button("ðŸ” Discover Files", width="stretch", type="secondary"):
            _discover_files()

        stats = st.session_state.get("da_folder_stats")
        if stats:
            st.caption(f"âœ… {stats.supported_files} supported / {stats.total_files} total files")
            for dtype, count in stats.files_by_type.items():
                st.caption(f"  â€¢ {dtype.upper()}: {count}")

        # --- Process ---
        st.subheader("4. Process")
        if st.button(
            "âš™ï¸ Process All Files",
            width="stretch",
            type="primary",
            disabled=not bool(st.session_state["da_discovered_files"]),
        ):
            _run_processing()

        # --- Output ---
        st.subheader("5. Output Format")
        format_options = {
            "Summary": "summary",
            "Executive Summary": "executive_summary",
            "Full Report": "report",
            "Presentation Outline": "presentation",
            "Document List": "list",
            "Database Entry (JSON)": "database_entry",
            "Knowledge Graph Export": "knowledge_graph",
            "Intelligence Brief": "new_brief",
            "Comparison Table": "comparison",
            "Timeline": "timeline",
        }
        selected_label = st.selectbox(
            "Generate as",
            options=list(format_options.keys()),
            index=list(format_options.values()).index(st.session_state["da_output_format"]),
        )
        st.session_state["da_output_format"] = format_options[selected_label]

        if st.button(
            "ðŸ“„ Generate Output",
            width="stretch",
            disabled=st.session_state["da_analysis"] is None,
        ):
            _generate_output()

        # --- Export ---
        st.subheader("6. Export")
        output = st.session_state.get("da_output")
        if output:
            st.download_button(
                "â¬‡ï¸ Download as Markdown",
                data=output.content.encode("utf-8"),
                file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
                width="stretch",
            )
            if output.structured_data:
                st.download_button(
                    "â¬‡ï¸ Download Structured JSON",
                    data=json.dumps(output.structured_data, indent=2, default=str).encode("utf-8"),
                    file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json",
                    width="stretch",
                )

        # --- Quick actions ---
        st.markdown("---")
        st.subheader("Quick Actions")
        if st.button("ðŸ  Back to Dashboard", width="stretch"):
            st.switch_page("streamlit_app.py")
        if st.button("ðŸ—‘ï¸ Clear All Results", width="stretch"):
            for key in ["da_analysis", "da_output", "da_discovered_files",
                        "da_folder_stats", "da_progress_log", "da_error"]:
                st.session_state[key] = _STATE_DEFAULTS[key]
            st.rerun()


# ---------------------------------------------------------------------------
# Processing functions
# ---------------------------------------------------------------------------

def _discover_files() -> None:
    folder = st.session_state.get("da_folder_path", "").strip()
    if not folder:
        st.session_state["da_error"] = "Please enter a folder path first."
        return

    st.session_state["da_error"] = None
    try:
        from document_analysis.folder_reader import FolderReader

        reader = FolderReader(
            recursive=st.session_state["da_recursive"],
            max_file_size_mb=st.session_state["da_max_file_mb"],
        )
        files = reader.discover_files(folder)
        stats = reader.get_folder_stats(folder)
        st.session_state["da_discovered_files"] = files
        st.session_state["da_folder_stats"] = stats
        st.session_state["da_selected_files"] = [f["path"] for f in files]
        _log(f"Discovered {len(files)} files in {folder}")
    except Exception as exc:  # noqa: BLE001
        st.session_state["da_error"] = str(exc)
        _log(f"Discovery error: {exc}")


def _run_processing() -> None:
    files = st.session_state.get("da_discovered_files", [])
    selected = st.session_state.get("da_selected_files", [f["path"] for f in files])
    folder = st.session_state.get("da_folder_path", "")

    if not selected:
        st.session_state["da_error"] = "No files selected for processing."
        return

    st.session_state["da_error"] = None
    st.session_state["da_processing"] = True

    try:
        from document_analysis.document_parser import DocumentParser
        from document_analysis.content_extractor import ContentExtractor
        from document_analysis.context_analyzer import ContextAnalyzer
        from document_analysis.cache import ProcessingCache
        from document_analysis.folder_reader import FolderReader

        parser = DocumentParser()
        extractor = ContentExtractor(use_spacy=False)
        analyzer = ContextAnalyzer()
        cache = ProcessingCache() if st.session_state["da_use_cache"] else None

        doc_infos = []
        progress = st.progress(0, text="Processing filesâ€¦")

        for i, file_path in enumerate(selected):
            _log(f"Parsing: {Path(file_path).name}")
            progress.progress((i + 1) / len(selected), text=f"Processing {i+1}/{len(selected)}: {Path(file_path).name}")

            # Try cache first
            doc_dict = cache.get(file_path) if cache else None
            if doc_dict:
                from document_analysis.models import DocumentInfo
                try:
                    doc_info = DocumentInfo.model_validate(doc_dict)
                    _log(f"  (from cache) {Path(file_path).name}")
                except Exception:
                    doc_dict = None

            if not doc_dict:
                doc_info = parser.parse(file_path)
                doc_info = extractor.enrich(doc_info)
                if cache:
                    cache.set(file_path, doc_info.model_dump(mode="json"))

            doc_infos.append(doc_info)

        progress.empty()

        reader = FolderReader(recursive=st.session_state["da_recursive"])
        stats = st.session_state.get("da_folder_stats") or reader.get_folder_stats(folder)

        analysis = analyzer.analyze_folder(doc_infos, folder, stats)
        st.session_state["da_analysis"] = analysis
        _log(f"Analysis complete: {len(doc_infos)} docs, {len(analysis.relationships)} relationships")

        if st.session_state["da_use_ai"]:
            from document_analysis.ai_enhancer import AIEnhancer
            ai = AIEnhancer()
            if ai.is_available:
                analysis.narrative = ai.generate_insights(analysis)
                _log("AI insights generated")

    except Exception as exc:  # noqa: BLE001
        import traceback
        st.session_state["da_error"] = str(exc)
        st.session_state["da_processing"] = False
        _log(f"Processing error: {traceback.format_exc()}")
        return

    st.session_state["da_processing"] = False
    st.rerun()


def _generate_output() -> None:
    analysis = st.session_state.get("da_analysis")
    if analysis is None:
        return

    try:
        from document_analysis.output_generator import OutputGenerator
        from document_analysis.models import OutputFormat

        gen = OutputGenerator()
        fmt = OutputFormat(st.session_state["da_output_format"])
        output = gen.generate(analysis, fmt)

        if st.session_state["da_use_ai"]:
            from document_analysis.ai_enhancer import AIEnhancer
            ai = AIEnhancer()
            if ai.is_available:
                output = ai.enhance_output(output)

        st.session_state["da_output"] = output
        _log(f"Output generated: {fmt.value} ({output.word_count} words)")
    except Exception as exc:  # noqa: BLE001
        st.session_state["da_error"] = str(exc)


# ---------------------------------------------------------------------------
# Main tabs
# ---------------------------------------------------------------------------

def _render_files_tab() -> None:
    files = st.session_state.get("da_discovered_files", [])
    if not files:
        st.info("No files discovered yet. Enter a folder path in the sidebar and click **Discover Files**.")
        return

    st.subheader(f"ðŸ“ {len(files)} Files Discovered")

    # File selection
    all_paths = [f["path"] for f in files]
    selected = st.session_state.get("da_selected_files", all_paths)

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Select All"):
            st.session_state["da_selected_files"] = all_paths
            st.rerun()
    with col2:
        if st.button("Deselect All"):
            st.session_state["da_selected_files"] = []
            st.rerun()

    # File table
    import pandas as pd

    rows = []
    for f in files:
        size_kb = f["size_bytes"] / 1024
        rows.append({
            "Selected": f["path"] in selected,
            "Name": f["name"],
            "Type": f["doc_type"].upper(),
            "Size (KB)": f"{size_kb:.1f}",
            "Modified": f["modified_at"][:10],
            "Oversized": "âš ï¸" if f.get("oversized") else "",
        })
    df = pd.DataFrame(rows)
    edited = st.data_editor(
        df,
        width="stretch",
        hide_index=True,
        column_config={"Selected": st.column_config.CheckboxColumn("âœ“", width="small")},
        key="da_file_table",
    )
    # Sync selection back to state
    new_selected = [files[i]["path"] for i, row in edited.iterrows() if row["Selected"]]
    st.session_state["da_selected_files"] = new_selected

    stats = st.session_state.get("da_folder_stats")
    if stats:
        st.markdown("---")
        cols = st.columns(4)
        cols[0].metric("Total Files", stats.total_files)
        cols[1].metric("Supported", stats.supported_files)
        cols[2].metric("Unsupported", stats.unsupported_files)
        size_mb = stats.total_size_bytes / (1024 * 1024)
        cols[3].metric("Total Size", f"{size_mb:.1f} MB")


def _render_analysis_tab() -> None:
    analysis = st.session_state.get("da_analysis")
    if analysis is None:
        st.info("Run processing first to see analysis results.")
        return

    st.subheader("ðŸ“Š Folder Analysis Results")

    # Key metrics
    cols = st.columns(4)
    total_words = sum(d.word_count for d in analysis.documents if not d.error)
    cols[0].metric("Documents", len(analysis.documents))
    cols[1].metric("Total Words", f"{total_words:,}")
    cols[2].metric("Cross-References", len(analysis.relationships))
    cols[3].metric("Timeline Events", len(analysis.timeline))

    st.markdown("---")

    # Narrative
    st.subheader("Narrative")
    st.write(analysis.narrative)

    # Themes
    if analysis.cross_themes:
        st.subheader("Cross-Document Themes")
        theme_cols = st.columns(min(5, len(analysis.cross_themes)))
        for i, theme in enumerate(analysis.cross_themes[:10]):
            theme_cols[i % len(theme_cols)].markdown(f"`{theme}`")

    # Errors
    if analysis.processing_errors:
        with st.expander(f"âš ï¸ {len(analysis.processing_errors)} processing error(s)", expanded=False):
            for err in analysis.processing_errors:
                st.warning(err)

    # Gaps / contradictions
    col1, col2 = st.columns(2)
    with col1:
        if analysis.gaps:
            st.subheader("Identified Gaps")
            for g in analysis.gaps:
                st.warning(g)
        else:
            st.success("No significant gaps identified.")
    with col2:
        if analysis.contradictions:
            st.subheader("Contradictions")
            for c in analysis.contradictions:
                st.error(c)
        else:
            st.success("No contradictions detected.")

    # Per-document details
    st.markdown("---")
    st.subheader("Per-Document Details")
    for doc in analysis.documents:
        icon = "âœ…" if not doc.error else "âŒ"
        label = f"{icon} {doc.file_name} ({doc.doc_type.value.upper()})"
        with st.expander(label, expanded=False):
            if doc.error:
                st.error(f"Parse error: {doc.error}")
            else:
                mc = st.columns(4)
                mc[0].metric("Words", f"{doc.word_count:,}")
                mc[1].metric("Pages", doc.page_count or "â€”")
                mc[2].metric("Entities", len(doc.entities))
                mc[3].metric("Topics", len(doc.topics))
                if doc.summary:
                    st.write("**Summary:**", doc.summary)
                if doc.topics:
                    st.write("**Topics:**", ", ".join(doc.topics[:10]))


def _render_output_tab() -> None:
    output = st.session_state.get("da_output")
    if output is None:
        st.info("Select an output format in the sidebar and click **Generate Output**.")
        if st.session_state.get("da_analysis"):
            if st.button("ðŸ“„ Generate Default Summary Now"):
                _generate_output()
                st.rerun()
        return

    st.subheader(f"ðŸ“„ {output.output_format.value.replace('_', ' ').title()}")

    cols = st.columns(3)
    cols[0].metric("Words", output.word_count)
    cols[1].caption(f"Generated: {output.generated_at.strftime('%H:%M:%S')}")
    if output.ai_enhanced:
        cols[2].success("AI Enhanced")

    st.markdown("---")

    # Render content
    if output.output_format.value == "database_entry":
        try:
            parsed = json.loads(output.content)
            st.json(parsed)
        except Exception:
            st.code(output.content, language="json")
    else:
        st.markdown(output.content)


def _render_relationships_tab() -> None:
    analysis = st.session_state.get("da_analysis")
    if analysis is None:
        st.info("Run processing first to see relationships.")
        return

    st.subheader("ðŸ•¸ï¸ Cross-Document Relationships")

    if not analysis.relationships:
        st.info("No cross-document entity relationships found.")
        return

    import pandas as pd

    rows = []
    for rel in analysis.relationships:
        rows.append({
            "Entity": rel.entity_a,
            "Relationship": rel.relationship_type,
            "Documents": len(rel.source_documents),
            "Strength": f"{rel.strength:.0%}",
            "Source Files": ", ".join(rel.source_documents[:3]),
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, width="stretch", hide_index=True)

    # Timeline
    if analysis.timeline:
        st.markdown("---")
        st.subheader("â±ï¸ Timeline")
        tl_rows = []
        for ev in analysis.timeline[:30]:
            tl_rows.append({
                "Date": ev.date,
                "Description": ev.description[:120],
                "Source": ev.source_document,
                "Confidence": f"{ev.confidence:.0%}",
            })
        st.dataframe(pd.DataFrame(tl_rows), width="stretch", hide_index=True)


def _render_raw_tab() -> None:
    analysis = st.session_state.get("da_analysis")
    if analysis is None:
        st.info("Run processing first to see raw data.")
        return

    st.subheader("ðŸ”¬ Raw Data")
    doc_names = [d.file_name for d in analysis.documents]
    selected_doc = st.selectbox("Select document", doc_names)

    doc = next((d for d in analysis.documents if d.file_name == selected_doc), None)
    if doc is None:
        return

    tab_text, tab_entities, tab_tables, tab_meta = st.tabs(["Raw Text", "Entities", "Tables", "Metadata"])

    with tab_text:
        if doc.raw_text:
            st.text_area("Extracted text", value=doc.raw_text[:5000], height=400, disabled=True)
            if len(doc.raw_text) > 5000:
                st.caption(f"Showing first 5,000 of {len(doc.raw_text):,} characters.")
        else:
            st.info("No text extracted.")

    with tab_entities:
        if doc.entities:
            import pandas as pd
            rows = [{"Text": e.text, "Type": e.entity_type.value, "Confidence": f"{e.confidence:.0%}", "Context": e.context[:80]} for e in doc.entities]
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        else:
            st.info("No entities extracted.")

    with tab_tables:
        if doc.tables:
            for i, tbl in enumerate(doc.tables):
                st.write(f"**Table {i + 1}**" + (f" â€” Sheet: {tbl.get('sheet', '')}" if tbl.get("sheet") else ""))
                rows = tbl.get("rows", [])
                if rows:
                    import pandas as pd
                    try:
                        header = rows[0] if len(rows) > 1 else [f"Col {j}" for j in range(len(rows[0]))]
                        df = pd.DataFrame(rows[1:], columns=header) if len(rows) > 1 else pd.DataFrame(rows)
                        st.dataframe(df, width="stretch", hide_index=True)
                    except Exception:
                        st.write(rows[:20])
        else:
            st.info("No tables extracted.")

    with tab_meta:
        meta = {
            "file_path": doc.file_path,
            "doc_type": doc.doc_type.value,
            "size_bytes": doc.size_bytes,
            "page_count": doc.page_count,
            "word_count": doc.word_count,
            "char_count": doc.char_count,
            "language": doc.language,
            "encoding": doc.encoding,
            "modified_at": str(doc.modified_at),
            "extracted_at": str(doc.extracted_at),
            "error": doc.error,
            **doc.metadata,
        }
        st.json(meta)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    _init_state()

    # Error banner
    err = st.session_state.get("da_error")
    if err:
        st.error(err)

    # Header
    col_h1, col_h2 = st.columns([6, 1])
    with col_h1:
        st.title("ðŸ“‚ Document Analysis")
        st.caption("Discover â†’ Parse â†’ Extract â†’ Analyse â†’ Export")
    with col_h2:
        _render_back_button()

    _render_sidebar()

    # Log expander
    logs = st.session_state.get("da_progress_log", [])
    if logs:
        with st.expander(f"Processing log ({len(logs)} entries)", expanded=False):
            for line in logs[-20:]:
                st.caption(line)

    st.markdown("---")

    # Main tabs
    tab_files, tab_analysis, tab_output, tab_relationships, tab_raw = st.tabs(
        ["ðŸ“ Files", "ðŸ“Š Analysis", "ðŸ“„ Output", "ðŸ•¸ï¸ Relationships", "ðŸ”¬ Raw Data"]
    )

    with tab_files:
        _render_files_tab()

    with tab_analysis:
        _render_analysis_tab()

    with tab_output:
        _render_output_tab()

    with tab_relationships:
        _render_relationships_tab()

    with tab_raw:
        _render_raw_tab()


main()

