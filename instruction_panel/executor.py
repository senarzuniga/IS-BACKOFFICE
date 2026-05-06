"""Executes parsed instructions by orchestrating document analysis modules."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from document_analysis.ai_enhancer import AIEnhancer
from document_analysis.content_extractor import ContentExtractor
from document_analysis.context_analyzer import ContextAnalyzer
from document_analysis.document_parser import DocumentParser
from document_analysis.folder_reader import FolderReader
from document_analysis.models import DocumentInfo, OutputFormat
from document_analysis.output_generator import OutputGenerator


def _to_output_format(output_type: str | None) -> OutputFormat:
    mapping = {
        "summary": OutputFormat.SUMMARY,
        "executive_summary": OutputFormat.EXECUTIVE_SUMMARY,
        "report": OutputFormat.REPORT,
        "presentation": OutputFormat.PRESENTATION,
        "list": OutputFormat.LIST,
        "table": OutputFormat.COMPARISON,
        "timeline": OutputFormat.TIMELINE,
        "comparison": OutputFormat.COMPARISON,
        "database": OutputFormat.DATABASE_ENTRY,
        "json": OutputFormat.DATABASE_ENTRY,
        "csv": OutputFormat.LIST,
        "markdown": OutputFormat.SUMMARY,
    }
    return mapping.get((output_type or "summary").lower(), OutputFormat.SUMMARY)


def _build_file_listing(discovered: list[dict[str, Any]]) -> str:
    """Build a markdown file listing from discovered file entries."""
    grouped: dict[str, list[str]] = {}
    for item in discovered:
        grouped.setdefault(item.get("doc_type", "unknown"), []).append(item.get("name", ""))
    lines = ["# Folder File List", f"Total files: {len(discovered)}", ""]
    for doc_type, names in sorted(grouped.items()):
        lines.append(f"## {doc_type.upper()} ({len(names)})")
        lines.extend(f"- {name}" for name in names[:200])
        lines.append("")
    return "\n".join(lines)


class InstructionExecutor:
    """Execute parsed instructions step by step."""

    def __init__(self) -> None:
        self.parser = DocumentParser()
        self.extractor = ContentExtractor(use_spacy=True)
        self.analyzer = ContextAnalyzer()
        self.generator = OutputGenerator()
        self.enhancer = AIEnhancer()

    def execute(
        self,
        parsed_instruction: dict[str, Any],
        progress_callback: Callable[[float], None] | None = None,
        status_callback: Callable[[str], None] | None = None,
    ) -> dict[str, Any]:
        steps: list[dict[str, Any]] = []

        context: dict[str, Any] = {
            "folder_path": parsed_instruction.get("folder_path"),
            "source_url": parsed_instruction.get("url"),
            "discovered_files": [],
            "parsed_documents": [],
            "extracted_entities": [],
            "folder_analysis": None,
            "generated_output": "",
            "folder_stats": None,
        }

        actions = parsed_instruction.get("actions", [])
        if not actions:
            actions = [
                {"action": "read_folder", "parameters": {}, "priority": 1},
                {"action": "parse_documents", "parameters": {}, "priority": 2},
                {"action": "analyze_content", "parameters": {}, "priority": 3},
                {
                    "action": "generate_output",
                    "parameters": {"type": parsed_instruction.get("output_type", "summary")},
                    "priority": 4,
                },
            ]

        sorted_actions = sorted(actions, key=lambda a: a.get("priority", 99))

        for i, action_def in enumerate(sorted_actions):
            action = action_def.get("action", "")
            params = action_def.get("parameters", {})
            step = {
                "step_number": i + 1,
                "description": self._describe_action(action, params),
                "status": "running",
                "result": None,
                "error": None,
                "duration_seconds": None,
            }
            steps.append(step)

            if status_callback:
                status_callback(f"Step {i + 1}/{len(sorted_actions)}: {step['description']}")

            started = datetime.now()
            try:
                result_message = self._execute_action(action, params, parsed_instruction, context)
                step["status"] = "completed"
                step["result"] = result_message
            except Exception as exc:  # noqa: BLE001
                step["status"] = "failed"
                step["error"] = str(exc)
                if status_callback:
                    status_callback(f"Error: {exc}")

            step["duration_seconds"] = (datetime.now() - started).total_seconds()

            if progress_callback:
                progress_callback((i + 1) / len(sorted_actions))

        if not context.get("generated_output") and context.get("folder_analysis") is not None:
            fmt = _to_output_format(parsed_instruction.get("output_type", "summary"))
            output = self.generator.generate(context["folder_analysis"], fmt)
            context["generated_output"] = output.content

        # Clean up any temporary directories created during execution (e.g. URL fetch)
        import shutil
        for tmp_dir in context.pop("_temp_dirs", []):
            try:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:  # noqa: BLE001
                pass

        return {
            "parsed_instruction": parsed_instruction,
            "steps": steps,
            "output_content": context.get("generated_output", ""),
            "output_files": [],
            "summary": self._generate_execution_summary(steps, context),
            "follow_up_suggestions": self._generate_suggestions(context, parsed_instruction),
            "total_duration_seconds": sum((s.get("duration_seconds") or 0.0) for s in steps),
            "context": context,
        }

    def _describe_action(self, action: str, params: dict[str, Any]) -> str:
        descriptions = {
            "fetch_url": "Fetching URL content",
            "read_folder": "Reading folder contents",
            "parse_documents": "Parsing document contents",
            "extract_entities": "Extracting entities and metadata",
            "analyze_content": "Analyzing content across documents",
            "generate_output": f"Generating {params.get('type', 'output')}",
            "compare_documents": "Comparing documents",
            "structure_data": "Structuring extracted data",
            "search": "Searching for specific information",
        }
        return descriptions.get(action, f"Executing action: {action}")

    def _execute_action(
        self,
        action: str,
        params: dict[str, Any],
        parsed_instruction: dict[str, Any],
        context: dict[str, Any],
    ) -> str:
        folder_path = context.get("folder_path")
        source_url = context.get("source_url")

        if action == "fetch_url":
            import tempfile
            import requests
            import ipaddress

            url = source_url or params.get("url", "")
            if not url:
                raise ValueError("No URL provided. Include a URL (http:// or https://) in your instruction.")
            if not url.lower().startswith(("http://", "https://")):
                raise ValueError(f"Only http:// and https:// URLs are allowed. Got: {url!r}")

            # Resolve hostname and block private/loopback ranges (SSRF protection)
            import socket
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            hostname = parsed_url.hostname or ""
            try:
                ip_str = socket.gethostbyname(hostname)
                ip = ipaddress.ip_address(ip_str)
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                    raise ValueError(f"Requests to private/internal addresses are not allowed: {ip_str}")
            except (socket.gaierror, ValueError) as exc:
                if "not allowed" in str(exc):
                    raise
                # DNS resolution failure is acceptable (will fail at requests.get)

            resp = requests.get(url, timeout=30)
            resp.raise_for_status()

            tmp_dir = tempfile.mkdtemp()
            tmp_path = os.path.join(tmp_dir, "page.html")
            with open(tmp_path, "wb") as fh:
                fh.write(resp.content)

            doc = self.parser.parse(tmp_path)
            # Override the file_name so it shows the URL origin in reports
            doc.file_name = url.split("//", 1)[-1][:80]
            doc = self.extractor.enrich(doc)

            from document_analysis.models import FolderStats, DocumentType

            stats = FolderStats(
                folder_path=url,
                total_files=1,
                supported_files=1,
                unsupported_files=0,
                total_size_bytes=len(resp.content),
                files_by_type={DocumentType.HTML.value: 1},
            )
            context["parsed_documents"] = [doc]
            context["folder_stats"] = stats
            context["folder_path"] = url
            context["discovered_files"] = [{"name": doc.file_name, "path": tmp_path, "doc_type": "html"}]
            # Store tmp_dir for cleanup after execution
            context.setdefault("_temp_dirs", []).append(tmp_dir)
            return f"Fetched {len(resp.content):,} bytes from {url}"

        if action == "read_folder":
            if not folder_path:
                raise ValueError("No folder path provided. Include a folder path in your instruction.")
            if not os.path.isdir(folder_path):
                raise ValueError(f"Folder not found: {folder_path}")

            file_types = parsed_instruction.get("filters", {}).get("file_types", [])
            extensions = [f".{ft.lower().lstrip('.')}" for ft in file_types] if file_types else None

            reader = FolderReader(recursive=params.get("recursive", True), max_file_size_mb=float(params.get("max_file_size_mb", 50)))
            files = reader.discover_files(folder_path, extensions=extensions)
            stats = reader.get_folder_stats(folder_path)

            context["discovered_files"] = files
            context["folder_stats"] = stats
            return f"Found {len(files)} supported files in {folder_path}"

        if action == "parse_documents":
            files = context.get("discovered_files", [])
            if not files:
                context["parsed_documents"] = []
                return "No supported files found to parse"

            parsed_docs: list[DocumentInfo] = []
            for file_info in files:
                doc = self.parser.parse(file_info["path"])
                doc = self.extractor.enrich(doc)
                parsed_docs.append(doc)

            context["parsed_documents"] = parsed_docs
            return f"Parsed {len(parsed_docs)} documents"

        if action == "extract_entities":
            docs: list[DocumentInfo] = context.get("parsed_documents", [])
            if not docs:
                raise ValueError("No parsed documents found. Run parse_documents first.")

            entities = [e for doc in docs for e in doc.entities]
            context["extracted_entities"] = entities
            entity_types = sorted({e.entity_type.value for e in entities})
            return f"Extracted {len(entities)} entities ({', '.join(entity_types) if entity_types else 'none'})"

        if action == "analyze_content":
            docs: list[DocumentInfo] = context.get("parsed_documents", [])
            stats = context.get("folder_stats")
            if stats is None:
                raise ValueError("Missing folder statistics. Run read_folder first.")

            analysis = self.analyzer.analyze_folder(docs, folder_path=folder_path, stats=stats)
            context["folder_analysis"] = analysis
            return f"Analysis complete: {len(analysis.cross_themes)} themes, {len(analysis.relationships)} relationships"

        if action == "generate_output":
            requested = params.get("type") or parsed_instruction.get("output_type", "summary")
            # Map client_brief to the new OutputFormat
            if requested == "client_brief":
                from document_analysis.models import OutputFormat as OF
                fmt = OF.CLIENT_BRIEF
            else:
                fmt = _to_output_format(requested)

            analysis = context.get("folder_analysis")
            discovered = context.get("discovered_files", [])

            if analysis is None:
                docs: list[DocumentInfo] = context.get("parsed_documents", [])
                stats = context.get("folder_stats")

                # Fast path: when files were discovered but not yet parsed (explore_folder
                # intent), build the file listing directly instead of creating an empty
                # FolderAnalysis whose document list would also be empty.
                if fmt == OutputFormat.LIST and discovered and not docs:
                    context["generated_output"] = _build_file_listing(discovered)
                    return f"Generated {fmt.value} ({len(discovered)} files listed)"

                if stats is not None:
                    analysis = self.analyzer.analyze_folder(docs, folder_path=folder_path or "", stats=stats)
                    context["folder_analysis"] = analysis

            if analysis is None:
                if fmt == OutputFormat.LIST and discovered:
                    context["generated_output"] = _build_file_listing(discovered)
                    return f"Generated {fmt.value} ({len(discovered)} files listed)"
                raise ValueError("No folder analysis available. Run analyze_content first.")

            output = self.generator.generate(analysis, fmt)

            if fmt in {OutputFormat.EXECUTIVE_SUMMARY, OutputFormat.PRESENTATION, OutputFormat.REPORT} and self.enhancer.is_available:
                output = self.enhancer.enhance_output(output)

            context["generated_output"] = output.content
            return f"Generated {fmt.value} ({output.word_count} words)"

        if action == "search":
            query = (params.get("query") or "").strip()
            if not query:
                return "No search query provided"
            docs: list[DocumentInfo] = context.get("parsed_documents", [])
            matches = [d.file_name for d in docs if query.lower() in d.raw_text.lower()]
            return f"Found '{query}' in {len(matches)} document(s): {', '.join(matches[:8])}"

        return f"Action '{action}' completed"

    def _generate_execution_summary(self, steps: list[dict[str, Any]], context: dict[str, Any]) -> str:
        total = len(steps)
        completed = sum(1 for s in steps if s["status"] == "completed")
        failed = sum(1 for s in steps if s["status"] == "failed")

        summary = f"Executed {total} steps: {completed} completed"
        if failed:
            summary += f", {failed} failed"

        files = len(context.get("discovered_files", []))
        docs = len(context.get("parsed_documents", []))
        entities = len(context.get("extracted_entities", []))

        if files:
            summary += f". Discovered {files} files"
        if docs:
            summary += f". Parsed {docs} documents"
        if entities:
            summary += f". Extracted {entities} entities"

        return summary

    def _generate_suggestions(self, context: dict[str, Any], parsed_instruction: dict[str, Any]) -> list[str]:
        suggestions: list[str] = []

        source_url = context.get("source_url")
        folder = context.get("folder_path") or "this folder"
        docs: list[DocumentInfo] = context.get("parsed_documents", [])
        analysis = context.get("folder_analysis")

        if source_url:
            suggestions.append(f"Create an executive summary from {source_url}")
            suggestions.append(f"Generate a client brief from {source_url}")
            suggestions.append(f"Make a presentation outline from {source_url}")
        elif docs:
            suggestions.append(f"Create an executive summary for {folder}")
            suggestions.append(f"Generate a client brief for {folder}")
            suggestions.append(f"Generate a comparison table for {folder}")

        if analysis is not None and getattr(analysis, "timeline", None):
            suggestions.append("Build a timeline from extracted dates")

        suggestions.append("Analyze a different folder")

        return suggestions[:5]
