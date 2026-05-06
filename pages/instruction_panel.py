"""Instruction Panel â€” Natural Language Command Center."""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st
import pandas as pd

# Make project root importable when this file is loaded as a Streamlit page
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from instruction_panel.executor import InstructionExecutor
from instruction_panel.instruction_parser import InstructionParser
from document_analysis.folder_reader import SUPPORTED_EXTENSIONS

st.set_page_config(page_title="Instruction Panel", page_icon="ðŸ’¬", layout="wide")


def _init_state() -> None:
    defaults: dict[str, Any] = {
        "ip_instruction_history": [],
        "ip_current_result": None,
        "ip_execution_steps": [],
        "ip_is_processing": False,
        "ip_instruction_input": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_resource
def get_parser() -> InstructionParser:
    return InstructionParser()


@st.cache_resource
def get_executor() -> InstructionExecutor:
    return InstructionExecutor()


def _examples() -> list[tuple[str, str]]:
    return [
        ("Explore folder", "Check C:\\Users\\Inaki Senar\\Documents and tell me what's inside"),
        ("Summarize docs", "Read all PDFs in C:\\Users\\Inaki Senar\\Documents and create a summary"),
        ("Executive analysis", "Analyze all documents in C:\\Users\\Inaki Senar\\Documents and create an executive summary"),
        ("Client brief from folder", "Analyze all documents in C:\\Users\\Inaki Senar\\Documents and create a client brief"),
        ("Presentation from folder", "Read all files in C:\\Users\\Inaki Senar\\Documents and generate a presentation outline"),
        ("Analyze a web page", "Analyze https://en.wikipedia.org/wiki/Artificial_intelligence and create a summary"),
        ("URL executive summary", "Fetch https://en.wikipedia.org/wiki/Artificial_intelligence and generate an executive summary"),
        ("URL client brief", "Analyze https://en.wikipedia.org/wiki/Artificial_intelligence and create a client brief for my presentation"),
        ("Extract and timeline", "Extract all names and dates from C:\\Users\\Inaki Senar\\Documents and make a timeline"),
        ("Compare specs", "Read the product specs folder, extract technical specifications, and generate a comparison table"),
    ]


def _quick_paths() -> list[str]:
    candidates = [
        os.path.expanduser("~\\Documents"),
        os.path.expanduser("~\\Desktop"),
        os.path.expanduser("~\\Downloads"),
        "C:\\Users\\Inaki Senar\\Documents\\Ingecart",
    ]
    return [p for p in candidates if os.path.exists(p)]


def _execute_instruction(instruction: str) -> None:
    parser = get_parser()
    executor = get_executor()

    with st.status("Processing instruction...", expanded=True) as status:
        st.write("Understanding instruction...")
        parsed = parser.parse(
            instruction,
            conversation_context=st.session_state["ip_instruction_history"][-5:],
        )

        if not parsed.get("folder_path") and not parsed.get("url"):
            status.update(label="Source required", state="error")
            st.error(
                "I could not find a valid folder path or URL in your instruction. "
                "Please include a folder path (e.g. C:\\Users\\you\\Documents) "
                "or a full URL (https://...) in your instruction."
            )
            st.session_state["ip_is_processing"] = False
            return

        if parsed.get("url"):
            st.write(f"URL: {parsed['url']}")
        elif parsed.get("folder_path"):
            st.write(f"Folder: {parsed['folder_path']}")
        st.write(f"Intent: {parsed.get('intent', 'custom')}")
        st.write(f"Output: {parsed.get('output_type', 'summary')}")

        progress = st.progress(0.0)
        line = st.empty()

        def on_progress(value: float) -> None:
            progress.progress(max(0.0, min(1.0, value)))

        def on_status(message: str) -> None:
            line.text(message)

        result = executor.execute(parsed, progress_callback=on_progress, status_callback=on_status)
        progress.progress(1.0)
        line.empty()

        st.session_state["ip_current_result"] = result
        st.session_state["ip_execution_steps"] = result.get("steps", [])
        st.session_state["ip_instruction_history"].append(
            {
                "user": instruction,
                "assistant": result.get("summary", ""),
                "instruction": instruction,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "summary": result.get("summary", ""),
                "output_type": parsed.get("output_type", "summary"),
            }
        )

        has_failed_step = any(step.get("status") == "failed" for step in result.get("steps", []))
        if has_failed_step:
            status.update(label="Instruction executed with errors", state="error")
        else:
            status.update(label="Instruction executed successfully", state="complete")


def _extract_folder_path_from_text(text: str) -> str | None:
    if not text.strip():
        return None

    quoted = re.findall(r"[\"']([A-Za-z]:\\[^\"']+|/[^\"']+)[\"']", text)
    for candidate in quoted:
        if os.path.exists(candidate):
            return candidate

    windows_match = re.search(r"([A-Za-z]:\\[^\n\r\"']+)", text)
    if windows_match:
        candidate = windows_match.group(1).strip().rstrip(" .;,")
        if os.path.exists(candidate):
            return candidate

    return None


def _diagnose_folder(folder_path: str) -> None:
    all_files: list[dict[str, Any]] = []
    for root, _dirs, files in os.walk(folder_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            try:
                size = os.path.getsize(file_path)
                modified = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
            except OSError:
                size = 0
                modified = "unavailable"

            ext = Path(file_name).suffix.lower()
            supported = ext in SUPPORTED_EXTENSIONS
            all_files.append(
                {
                    "File": file_name,
                    "Extension": ext,
                    "Size (KB)": round(size / 1024, 2),
                    "Modified": modified,
                    "Supported": "yes" if supported else "unknown (raw fallback)",
                    "Detected Type": SUPPORTED_EXTENSIONS.get(ext).value if supported else "unknown",
                    "Full Path": file_path,
                }
            )

    with st.expander(f"Folder Diagnostic: {folder_path}", expanded=True):
        if not all_files:
            st.warning("No files found in this folder (including subfolders).")
            return

        df = pd.DataFrame(all_files)
        st.dataframe(df, width="stretch")

        unknown = [f for f in all_files if f["Supported"] != "yes"]
        st.caption(f"Total files: {len(all_files)} | Unknown extensions: {len(unknown)}")
        if unknown:
            st.info("Unknown extensions will still be attempted via raw text fallback parser.")


def _render_results() -> None:
    result = st.session_state.get("ip_current_result")
    if not result:
        st.info("Ready to run. Type an instruction and click Execute.")
        return

    with st.expander("Execution Details", expanded=False):
        for step in result.get("steps", []):
            icon = "OK" if step.get("status") == "completed" else "ERR" if step.get("status") == "failed" else "..."
            line = f"{icon} {step.get('description', '')}"
            if step.get("duration_seconds") is not None:
                line += f" ({step['duration_seconds']:.2f}s)"
            st.write(line)
            if step.get("error"):
                st.error(step["error"])
            elif step.get("result"):
                st.caption(step["result"])

    st.subheader("Output")
    output_content = result.get("output_content", "")
    if output_content:
        st.markdown(output_content)

        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "Download Markdown",
                data=output_content,
                file_name=f"instruction_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                width="stretch",
            )
        with c2:
            st.download_button(
                "Download Text",
                data=output_content,
                file_name=f"instruction_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                width="stretch",
            )
    else:
        st.warning("No output content generated. Review execution details for errors.")

    suggestions = result.get("follow_up_suggestions", [])
    if suggestions:
        st.markdown("### Follow-up Suggestions")
        for idx, suggestion in enumerate(suggestions):
            if st.button(f"{suggestion}", key=f"ip_follow_{idx}", width="stretch"):
                st.session_state["ip_instruction_input"] = suggestion
                st.rerun()


def _render_history() -> None:
    history = st.session_state.get("ip_instruction_history", [])
    if not history:
        return

    with st.expander(f"Instruction History ({len(history)})", expanded=False):
        for idx, item in enumerate(reversed(history[-10:])):
            st.caption(f"{item.get('timestamp', '')} | {item.get('output_type', 'summary')}")
            st.write(item.get("instruction", ""))
            st.caption(item.get("summary", ""))
            if st.button("Re-run", key=f"ip_rerun_{idx}"):
                st.session_state["ip_instruction_input"] = item.get("instruction", "")
                st.rerun()
            st.markdown("---")


def main() -> None:
    _init_state()

    st.title("Instruction Panel")
    st.caption("Natural language command center for folder discovery, document analysis, and output generation.")

    col_main, col_side = st.columns([2, 1])

    with col_main:
        with st.expander("Example Instructions", expanded=False):
            for idx, (label, example) in enumerate(_examples()):
                if st.button(label, key=f"ip_example_{idx}", width="stretch"):
                    st.session_state["ip_instruction_input"] = example
                    st.rerun()
                st.caption(example)

        instruction = st.text_area(
            "Instruction",
            value=st.session_state.get("ip_instruction_input", ""),
            placeholder="Check folder C:\\..., analyze all documents, and create an executive summary",
            height=120,
            key="ip_input_area",
        )
        st.session_state["ip_instruction_input"] = instruction

        execute_clicked = st.button(
            "Execute Instruction",
            type="primary",
            width="stretch",
            disabled=st.session_state.get("ip_is_processing", False) or not instruction.strip(),
        )

        if execute_clicked and instruction.strip():
            st.session_state["ip_is_processing"] = True
            st.session_state["ip_current_result"] = None
            _execute_instruction(instruction.strip())
            st.session_state["ip_is_processing"] = False

        _render_results()
        _render_history()

    with col_side:
        st.subheader("Capabilities")
        st.markdown(
            "\n".join(
                [
                    "- Analyze local folders or web URLs",
                    "- Parse PDF, DOCX, XLSX, CSV, TXT, JSON, XML, HTML, PPTX",
                    "- Extract entities, topics, and summaries",
                    "- Analyze cross-document relationships",
                    "- Generate: summary, executive summary, **client brief**, report, presentation, timeline, comparison",
                    "- Optional AI enhancement with OPENAI_API_KEY",
                    "",
                    "**URL examples:**",
                    "- Analyze https://... and create a summary",
                    "- Fetch https://... and generate an executive summary",
                    "- Analyze https://... and create a client brief",
                ]
            )
        )

        st.subheader("Quick Folder Browser")
        for p in _quick_paths():
            label = Path(p).name or p
            if st.button(f"Use {label}", key=f"ip_quick_{p}", width="stretch"):
                st.session_state["ip_instruction_input"] = f"Check {p} and tell me what's inside"
                st.rerun()

        st.subheader("Diagnostics")
        if st.button("Diagnose Folder", width="stretch"):
            folder_path = _extract_folder_path_from_text(st.session_state.get("ip_instruction_input", ""))
            if not folder_path:
                st.warning("No valid folder path detected in the instruction text.")
            elif not os.path.exists(folder_path):
                st.error(f"Folder does not exist: {folder_path}")
            else:
                _diagnose_folder(folder_path)

        if st.button("Back To Main App", width="stretch"):
            st.switch_page("streamlit_app.py")


main()

