from __future__ import annotations

import asyncio
import json
import re
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

st.set_page_config(layout="wide", page_title="IS-BACKOFFICE", page_icon="IA")

from backoffice.ui.components.results import render_main_content
from backoffice.ui.components.sidebar import render_sidebar


def _initialize_state() -> None:
    defaults: dict[str, Any] = {
        "current_workflow": "",
        "current_action": "",
        "last_result": None,
        "last_payload": {},
        "processing_queue": [],
        "last_activity": datetime.now().isoformat(timespec="seconds"),
        "status_logs": ["UI initialized"],
        "last_error": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _append_log(message: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state["status_logs"].append(f"[{ts}] {message}")
    st.session_state["last_activity"] = datetime.now().isoformat(timespec="seconds")


def _slugify_file_name(name: str, fallback: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", name.strip()).strip("._")
    return normalized or fallback


def _save_text_file(target_dir: str | Path, file_name: str, content: str, suffix: str) -> str:
    output_dir = Path(target_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{file_name}{suffix}"
    target.write_text(content, encoding="utf-8")
    return str(target)


def _run_folder_scan(payload: dict[str, Any]) -> dict[str, Any]:
    from document_analysis.folder_reader import FolderReader

    folder_path = (payload.get("folder_path") or "").strip()
    if not folder_path:
        raise ValueError("Folder path is required.")

    reader = FolderReader(
        recursive=bool(payload.get("recursive", True)),
        max_file_size_mb=float(payload.get("max_file_size_mb", 50)),
    )
    files = reader.discover_files(folder_path, recursive=bool(payload.get("recursive", True)))
    stats = reader.get_folder_stats(folder_path)

    return {
        "kind": "folder_scan",
        "workflow": "Workspace Reader",
        "action": "Scan folder",
        "status": "complete",
        "summary": f"Found {len(files)} files in {folder_path}.",
        "folder_path": folder_path,
        "files": files,
        "folder_stats": stats.model_dump(),
    }


def _build_folder_analysis(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    from document_analysis.content_extractor import ContentExtractor
    from document_analysis.context_analyzer import ContextAnalyzer
    from document_analysis.document_parser import DocumentParser
    from document_analysis.folder_reader import FolderReader

    folder_path = (payload.get("folder_path") or "").strip()
    if not folder_path:
        raise ValueError("Folder path is required.")

    recursive = bool(payload.get("recursive", True))
    max_file_size_mb = float(payload.get("max_file_size_mb", 50))
    reader = FolderReader(recursive=recursive, max_file_size_mb=max_file_size_mb)
    files = reader.discover_files(folder_path, recursive=recursive)
    stats = reader.get_folder_stats(folder_path)

    parser = DocumentParser()
    extractor = ContentExtractor(use_spacy=False)
    analyzer = ContextAnalyzer()

    documents = []
    for file_info in files:
        document = parser.parse(file_info["path"])
        documents.append(extractor.enrich(document))

    analysis = analyzer.analyze_folder(documents, folder_path=folder_path, stats=stats)
    return files, stats.model_dump(), analysis.model_dump()


def _run_folder_analysis(payload: dict[str, Any]) -> dict[str, Any]:
    files, stats, analysis = _build_folder_analysis(payload)
    return {
        "kind": "folder_analysis",
        "workflow": "Workspace Reader",
        "action": "Analyze folder",
        "status": "complete",
        "summary": analysis.get("narrative") or "Folder analysis complete.",
        "folder_path": payload.get("folder_path", ""),
        "files": files,
        "folder_stats": stats,
        "analysis": analysis,
        "include_entity_preview": bool(payload.get("include_entity_preview", True)),
    }


def _run_document_factory(payload: dict[str, Any]) -> dict[str, Any]:
    from document_analysis.ai_enhancer import AIEnhancer
    from document_analysis.models import FolderAnalysis, OutputFormat
    from document_analysis.output_generator import OutputGenerator

    files, stats, analysis_data = _build_folder_analysis(payload)
    analysis = FolderAnalysis.model_validate(analysis_data)
    output_format = OutputFormat(payload.get("output_format", "summary"))
    output = OutputGenerator().generate(analysis, output_format)

    ai_requested = bool(payload.get("use_ai", False))
    ai_available = False
    ai_insights = ""
    if ai_requested:
        enhancer = AIEnhancer()
        ai_available = enhancer.is_available
        if enhancer.is_available:
            output = enhancer.enhance_output(output)
        ai_insights = enhancer.generate_insights(analysis)
        if ai_insights and output.output_format.value != "database_entry":
            output.content = f"{output.content}\n\n## Strategic Insights\n{ai_insights}"
            output.word_count = len(output.content.split())

    saved_to = None
    if payload.get("save_output"):
        base_name = _slugify_file_name(payload.get("output_name", "generated_output"), "generated_output")
        output_dir = payload.get("output_directory") or payload.get("folder_path") or "."
        suffix = ".json" if output.output_format.value == "database_entry" else ".md"
        content_to_save = output.content
        if suffix == ".json":
            parsed_json = json.loads(output.content)
            content_to_save = json.dumps(parsed_json, indent=2, ensure_ascii=False)
        saved_to = _save_text_file(output_dir, base_name, content_to_save, suffix)

    return {
        "kind": "document_output",
        "workflow": "Document Factory",
        "action": "Create document",
        "status": "complete",
        "summary": f"Created {output.output_format.value.replace('_', ' ')} from {len(files)} file(s).",
        "folder_path": payload.get("folder_path", ""),
        "files": files,
        "folder_stats": stats,
        "analysis": analysis.model_dump(),
        "output": output.model_dump(),
        "ai_requested": ai_requested,
        "ai_available": ai_available,
        "ai_insights": ai_insights,
        "saved_to": saved_to,
    }


def _run_web_intelligence(payload: dict[str, Any]) -> dict[str, Any]:
    from backoffice.ingestion.intelligence.agents.extractor_agent import ExtractorAgent
    from backoffice.ingestion.intelligence.agents.intelligence_agent import IntelligenceAgent
    from backoffice.ingestion.intelligence.agents.normalizer_agent import NormalizerAgent
    from backoffice.ingestion.intelligence.agents.scraper_agent import ScraperAgent

    url = (payload.get("url") or "").strip()
    if not url:
        raise ValueError("Target URL is required.")

    async def _scrape_once() -> tuple[Any, Any, list[Any]]:
        scraper = ScraperAgent()
        extractor = ExtractorAgent(None)
        normalizer = NormalizerAgent()
        intelligence = IntelligenceAgent(None)

        scrape_result = await scraper.scrape(
            url=url,
            source_id="sidebar_manual",
            source_name="Sidebar Manual Trigger",
            scraper_type=payload.get("scraper_type", "static"),
        )
        if not scrape_result.success or not scrape_result.html_content:
            raise ValueError(scrape_result.error_message or "Scraping failed.")

        extracted = await extractor.extract(
            html=scrape_result.html_content,
            source_id="sidebar_manual",
            source_name="Sidebar Manual Trigger",
            url=url,
            data_type=payload.get("data_type", "product"),
        )
        normalized = await normalizer.normalize(extracted)
        outputs = await intelligence.analyze_record(
            source_id=normalized.source_id,
            source_name=normalized.source_name,
            source_url=normalized.url,
            payload=normalized.normalized_content,
        )
        return scrape_result, normalized, outputs

    loop = asyncio.new_event_loop()
    try:
        scrape_result, normalized, outputs = loop.run_until_complete(_scrape_once())
    finally:
        loop.close()

    intelligence_rows = [
        {
            "type": item.output_type,
            "title": item.title,
            "description": item.description,
            "impact": item.impact,
            "suggested_action": item.suggested_action,
        }
        for item in outputs
    ]

    saved_to = None
    if payload.get("save_output"):
        brief_lines = [
            "# Web Intelligence Brief",
            f"Source URL: {url}",
            f"Scraper mode: {payload.get('scraper_type', 'static')}",
            f"Expected data: {payload.get('data_type', 'product')}",
            "",
            "## Structured Extraction",
            json.dumps(normalized.normalized_content, indent=2, ensure_ascii=False, default=str),
            "",
            "## Intelligence Signals",
        ]
        if intelligence_rows:
            for item in intelligence_rows:
                brief_lines.append(f"- {item['title']}: {item['description']} ({item['impact']})")
                brief_lines.append(f"  Action: {item['suggested_action']}")
        else:
            brief_lines.append("- No intelligence signals generated.")

        base_name = _slugify_file_name(payload.get("output_name", "web_intelligence_brief"), "web_intelligence_brief")
        output_dir = payload.get("output_directory") or "."
        saved_to = _save_text_file(output_dir, base_name, "\n".join(brief_lines), ".md")

    return {
        "kind": "web_intelligence",
        "workflow": "Web Intelligence",
        "action": "Scrape URL",
        "status": "complete",
        "summary": f"Scraped {url} and generated {len(intelligence_rows)} intelligence output(s).",
        "url": url,
        "scraper": {
            "scraper_type": scrape_result.scraper_type,
            "response_time_ms": scrape_result.response_time_ms,
            "status_code": scrape_result.status_code,
        },
        "extracted": normalized.normalized_content,
        "confidence_score": normalized.confidence_score,
        "intelligence": intelligence_rows,
        "saved_to": saved_to,
    }


def _run_selected_action(sidebar_state: dict[str, Any]) -> None:
    workflow = sidebar_state.get("workflow", "")
    action = sidebar_state.get("action", "")
    payload = sidebar_state.get("payload", {})

    if not workflow or not action:
        return

    try:
        if workflow == "Workspace Reader" and action == "Scan folder":
            result = _run_folder_scan(payload)
        elif workflow == "Workspace Reader" and action == "Analyze folder":
            result = _run_folder_analysis(payload)
        elif workflow == "Document Factory" and action == "Create document":
            result = _run_document_factory(payload)
        elif workflow == "Web Intelligence" and action == "Scrape URL":
            result = _run_web_intelligence(payload)
        else:
            raise ValueError(f"Unsupported workflow: {workflow} / {action}")

        st.session_state["current_workflow"] = workflow
        st.session_state["current_action"] = action
        st.session_state["last_payload"] = payload
        st.session_state["last_result"] = result
        st.session_state["processing_queue"].append(
            {
                "workflow": workflow,
                "action": action,
                "status": result.get("status", "complete"),
                "time": datetime.now().isoformat(timespec="seconds"),
            }
        )
        st.session_state["last_error"] = None
        _append_log(f"Completed workflow: {workflow} / {action}")
        st.rerun()
    except Exception as exc:  # noqa: BLE001
        st.session_state["last_error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "trace": traceback.format_exc(),
        }
        _append_log(f"Workflow failed: {workflow} / {action} -> {type(exc).__name__}")


def _render_error_state() -> None:
    error = st.session_state.get("last_error")
    if not error:
        return

    st.error(f"{error['type']}: {error['message']}")
    with st.expander("Stack trace", expanded=False):
        st.code(error["trace"], language="text")


def _handle_quick_action(label: str) -> None:
    if label == "Document Analysis":
        st.switch_page("pages/document_analysis.py")
        return
    if label == "Instruction Panel":
        st.switch_page("pages/instruction_panel.py")
        return
    if label == "Dashboard":
        st.session_state["current_workflow"] = ""
        st.session_state["current_action"] = ""
        st.session_state["last_result"] = None
        st.rerun()


def _render_status_bar() -> None:
    st.markdown("---")
    with st.expander("Run Log", expanded=True):
        queue = st.session_state.get("processing_queue", [])
        st.caption(f"Executed workflows: {len(queue)}")
        for line in st.session_state.get("status_logs", [])[-12:]:
            st.write(line)


def main() -> None:
    _initialize_state()

    st.markdown("# IS-BACKOFFICE")
    st.caption(
        "Focused on the three workflows the current application can execute end-to-end: local folder intelligence, document generation, and web intelligence scraping."
    )

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
