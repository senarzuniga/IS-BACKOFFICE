"""Parses natural language instructions into structured commands.

Uses rule-based extraction first, then optional LLM enrichment for deeper intent
understanding when OpenAI credentials are available.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from models.instruction import InstructionIntent, OutputType


class InstructionParser:
    """Parse natural language instructions into structured actions."""

    def __init__(self, llm_provider: str | None = None) -> None:
        self.llm_provider = llm_provider or os.getenv("LLM_PROVIDER", "openai")

    def parse(self, instruction_text: str, conversation_context: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        url = self._extract_url(instruction_text)
        folder_path = None if url else self._extract_folder_path(instruction_text)
        file_types = self._extract_file_types(instruction_text)
        output_type = self._extract_output_type(instruction_text)
        intent = self._detect_intent(instruction_text)

        llm_analysis = self._analyze_with_llm(instruction_text, conversation_context)

        resolved_intent = intent or llm_analysis.get("intent") or InstructionIntent.CUSTOM.value
        resolved_output = output_type or llm_analysis.get("output_type") or OutputType.SUMMARY.value
        if resolved_intent == InstructionIntent.EXPLORE_FOLDER.value and not output_type and not llm_analysis.get("output_type"):
            resolved_output = OutputType.LIST.value

        # When a URL is provided, override the action plan to fetch the URL first
        if url:
            if not resolved_intent or resolved_intent == InstructionIntent.CUSTOM.value:
                resolved_intent = InstructionIntent.ANALYZE_DOCUMENTS.value
            actions = self._url_action_plan(resolved_output)
        else:
            actions = llm_analysis.get("actions") or self._default_action_plan(resolved_intent)

        # Ensure any generate_output action uses the resolved output type.
        for action in actions:
            if action.get("action") == "generate_output":
                params = action.setdefault("parameters", {})
                params["type"] = resolved_output

        result = {
            "folder_path": folder_path or (None if url else llm_analysis.get("folder_path")),
            "url": url,
            "intent": resolved_intent,
            "actions": actions,
            "output_type": resolved_output,
            "filters": {
                "file_types": file_types or llm_analysis.get("file_types", []),
                **llm_analysis.get("filters", {}),
            },
            "special_instructions": instruction_text,
            "confidence": float(llm_analysis.get("confidence", 0.7)),
        }
        return result

    def _extract_url(self, text: str) -> str | None:
        """Extract the first http/https URL from the instruction text."""
        match = re.search(r"https?://[^\s\"',;<>\]]+", text, re.IGNORECASE)
        if match:
            url = match.group()
            # Strip common trailing punctuation that is not part of the URL,
            # but preserve ) that closes a ( opened inside the URL itself.
            url = url.rstrip(".,;")
            # Remove a trailing ) only when there is no matching ( in the URL
            while url.endswith(")") and url.count("(") < url.count(")"):
                url = url[:-1]
            return url
        return None

    def _extract_folder_path(self, text: str) -> str | None:
        quoted = re.findall(r"[\"']([A-Za-z]:\\[^\"']+|/[^\"']+)[\"']", text)
        for candidate in quoted:
            p = self._resolve_path(candidate)
            if p:
                return p

        # Greedy match first, then progressively trim trailing natural-language suffixes.
        windows_paths = re.findall(r"([A-Za-z]:\\[^\n\r\"']+)", text)
        windows_paths.sort(key=len, reverse=True)
        for candidate in windows_paths:
            for normalized in self._candidate_path_variants(candidate):
                p = self._resolve_path(normalized)
                if p:
                    return p

        # Unquoted Unix/Linux absolute paths (e.g. /home/user/docs or /tmp/project)
        unix_paths = re.findall(r"(?<!\w)((?:/[a-zA-Z0-9._\-]+){2,}/?)", text)
        unix_paths.sort(key=len, reverse=True)
        for candidate in unix_paths:
            for normalized in self._candidate_path_variants_unix(candidate.rstrip("/")):
                p = self._resolve_path(normalized)
                if p:
                    return p

        named_patterns = [
            r"(?:the\s+)?folder\s+(?:called|named|at|path)?\s*[\"']?([^\"',.;]+)[\"']?",
            r"check\s+[\"']?([A-Za-z]:[^\"',.;]+|/[a-zA-Z0-9._/\-]+)[\"']?",
            r"inside\s+[\"']?([A-Za-z]:[^\"',.;]+|/[a-zA-Z0-9._/\-]+)[\"']?",
            r"read\s+[\"']?([A-Za-z]:[^\"',.;]+|/[a-zA-Z0-9._/\-]+)[\"']?",
            r"analy(?:s|z)e\s+[\"']?([A-Za-z]:[^\"',.;]+|/[a-zA-Z0-9._/\-]+)[\"']?",
            r"in\s+[\"']?([A-Za-z]:[^\"',.;\n\r]+|/[a-zA-Z0-9._/\-]+)[\"']?",
        ]
        for pattern in named_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                candidate = match.group(1).strip().rstrip("\\/")
                for normalized in self._candidate_path_variants(candidate):
                    p = self._resolve_path(normalized)
                    if p:
                        return p

        return None

    def _extract_file_types(self, text: str) -> list[str]:
        file_type_map = {
            "pdf": "pdf",
            "pdfs": "pdf",
            "excel": "xlsx",
            "spreadsheet": "xlsx",
            "xlsx": "xlsx",
            "xls": "xlsx",
            "word": "docx",
            "document": "docx",
            "docx": "docx",
            "doc": "docx",
            "powerpoint": "pptx",
            "presentation": "pptx",
            "ppt": "pptx",
            "pptx": "pptx",
            "csv": "csv",
            "text": "txt",
            "txt": "txt",
            "json": "json",
            "xml": "xml",
            "html": "html",
        }

        found: set[str] = set()
        text_lower = text.lower()
        for keyword, filetype in file_type_map.items():
            if re.search(rf"\b{re.escape(keyword)}\b", text_lower):
                found.add(filetype)

        return sorted(found)

    def _extract_output_type(self, text: str) -> str | None:
        output_patterns = {
            "client_brief": ["client brief", "client document", "for the client", "client report", "client presentation", "client-ready", "client facing", "for my client"],
            OutputType.EXECUTIVE_SUMMARY.value: ["executive summary", "exec summary", "one-pager", "one pager"],
            OutputType.PRESENTATION.value: ["presentation", "presentation outline", "slide deck", "slides", "ppt"],
            OutputType.REPORT.value: ["report", "detailed report", "full report", "write up"],
            OutputType.TIMELINE.value: ["timeline", "chronolog", "sequence of events", "order by date"],
            OutputType.COMPARISON.value: ["compare", "comparison", "side by side", "versus", "vs"],
            OutputType.TABLE.value: ["table", "spreadsheet", "grid", "matrix", "tabular"],
            OutputType.LIST.value: ["list", "listing", "inventory", "catalog", "catalogue", "what's inside", "whats inside", "inside"],
            OutputType.JSON.value: ["json", "structured data", "machine readable"],
            OutputType.CSV.value: ["csv", "export to csv"],
            OutputType.DATABASE.value: ["database", "db entries", "import to database"],
            OutputType.SUMMARY.value: ["summarize", "summary", "overview", "brief", "digest"],
        }

        text_lower = text.lower()
        for out_type, keywords in output_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return out_type
        return None

    def _detect_intent(self, text: str) -> str | None:
        intent_patterns = {
            InstructionIntent.EXPLORE_FOLDER.value: ["what is in", "whats in", "what's in", "what's inside", "list files", "show me what", "browse", "contents of", "inside the folder"],
            InstructionIntent.EXTRACT_INFO.value: ["extract", "pull out", "get the", "find all the", "collect", "gather"],
            InstructionIntent.ANALYZE_DOCUMENTS.value: ["analyze", "analyse", "examine", "review", "study", "look into"],
            InstructionIntent.GENERATE_OUTPUT.value: ["generate", "create", "make", "produce", "build", "write"],
            InstructionIntent.COMPARE_DOCUMENTS.value: ["compare", "differences between", "similarities", "side by side"],
            InstructionIntent.FIND_SPECIFIC.value: ["find", "search for", "locate", "look for", "where is"],
            InstructionIntent.STRUCTURE_DATA.value: ["structure", "organize", "categorize", "classify", "sort"],
            InstructionIntent.CREATE_REPORT.value: ["report on", "report about", "make a report"],
            InstructionIntent.CREATE_PRESENTATION.value: ["presentation", "deck", "slides"],
            InstructionIntent.SUMMARIZE.value: ["summarize", "sum up", "tldr", "give me the gist", "recap"],
        }

        text_lower = text.lower()
        for intent, keywords in intent_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return intent
        return None

    def _analyze_with_llm(self, instruction: str, context: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        if self.llm_provider != "openai":
            return {"confidence": 0.3}

        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            return {"confidence": 0.3}

        system_prompt = (
            "You are an instruction parser for a document analysis system. "
            "Return only valid JSON with fields: folder_path, url, intent, actions, "
            "output_type, file_types, filters, special_requirements, confidence. "
            "Valid output_type values include: summary, executive_summary, report, "
            "presentation, list, timeline, comparison, database, json, csv, client_brief."
        )

        context_str = ""
        if context:
            recent = context[-3:]
            context_str = "\n".join(
                f"User: {item.get('user', '')}\nAssistant: {item.get('assistant', '')}" for item in recent
            )

        user_prompt = (
            f"{context_str}\n"
            f"Current instruction: {instruction}\n"
            "Return JSON only."
        )

        try:
            raw = self._call_llm(system_prompt, user_prompt, api_key=api_key)
            match = re.search(r"\{[\s\S]*\}", raw)
            if not match:
                return {"confidence": 0.3}
            data = json.loads(match.group())
            return data if isinstance(data, dict) else {"confidence": 0.3}
        except Exception:
            return {"confidence": 0.3}

    def _call_llm(self, system_prompt: str, user_prompt: str, api_key: str) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=1000,
        )
        return response.choices[0].message.content or "{}"

    def _url_action_plan(self, output_type: str) -> list[dict[str, Any]]:
        """Return the action plan used when a URL is provided as the source."""
        return [
            {"action": "fetch_url", "parameters": {}, "priority": 1},
            {"action": "extract_entities", "parameters": {}, "priority": 2},
            {"action": "analyze_content", "parameters": {}, "priority": 3},
            {"action": "generate_output", "parameters": {"type": output_type}, "priority": 4},
        ]

    def _default_action_plan(self, intent: str) -> list[dict[str, Any]]:
        plans = {
            InstructionIntent.EXPLORE_FOLDER.value: [
                {"action": "read_folder", "parameters": {}, "priority": 1},
                {"action": "generate_output", "parameters": {"type": "list"}, "priority": 2},
            ],
            InstructionIntent.SUMMARIZE.value: [
                {"action": "read_folder", "parameters": {}, "priority": 1},
                {"action": "parse_documents", "parameters": {}, "priority": 2},
                {"action": "analyze_content", "parameters": {}, "priority": 3},
                {"action": "generate_output", "parameters": {"type": "summary"}, "priority": 4},
            ],
            InstructionIntent.ANALYZE_DOCUMENTS.value: [
                {"action": "read_folder", "parameters": {}, "priority": 1},
                {"action": "parse_documents", "parameters": {}, "priority": 2},
                {"action": "extract_entities", "parameters": {}, "priority": 3},
                {"action": "analyze_content", "parameters": {}, "priority": 4},
                {"action": "generate_output", "parameters": {"type": "report"}, "priority": 5},
            ],
            InstructionIntent.EXTRACT_INFO.value: [
                {"action": "read_folder", "parameters": {}, "priority": 1},
                {"action": "parse_documents", "parameters": {}, "priority": 2},
                {"action": "extract_entities", "parameters": {}, "priority": 3},
                {"action": "generate_output", "parameters": {"type": "list"}, "priority": 4},
            ],
        }

        return plans.get(
            intent,
            [
                {"action": "read_folder", "parameters": {}, "priority": 1},
                {"action": "parse_documents", "parameters": {}, "priority": 2},
                {"action": "analyze_content", "parameters": {}, "priority": 3},
                {"action": "generate_output", "parameters": {"type": "summary"}, "priority": 4},
            ],
        )

    def _resolve_path(self, candidate: str) -> str | None:
        candidate = candidate.strip().strip('"').strip("'")
        p = Path(candidate).expanduser()
        if p.exists():
            return str(p.resolve())

        for base in [Path.cwd(), Path.home(), Path("C:/")]:
            merged = (base / candidate).resolve()
            if merged.exists():
                return str(merged)

        # Preserve explicit absolute paths even when they do not exist yet,
        # so the executor can return a precise "Folder not found" error.
        if re.match(r"^[A-Za-z]:\\", candidate) or candidate.startswith("/"):
            return candidate.rstrip("\\")

        return None

    def _candidate_path_variants(self, candidate: str) -> list[str]:
        candidate = candidate.strip().strip('"').strip("'")
        variants: list[str] = []

        split_markers = [",", " and ", " then ", " to ", " where ", " that ", " for "]
        lowered = candidate.lower()
        for marker in split_markers:
            idx = lowered.find(marker)
            if idx > 2:
                variants.append(candidate[:idx].rstrip(" .;,").rstrip("\\"))

        # Also progressively trim by path separators in case extra tokens were appended.
        parts = re.split(r"\\+", candidate)
        while len(parts) > 2:
            parts = parts[:-1]
            variants.append("\\".join(parts))

        # Last resort: original candidate.
        variants.append(candidate)

        deduped = []
        seen = set()
        for item in variants:
            key = item.lower()
            if key not in seen and item:
                seen.add(key)
                deduped.append(item)
        return deduped

    def _candidate_path_variants_unix(self, candidate: str) -> list[str]:
        """Build progressively shorter path variants for Unix-style absolute paths."""
        candidate = candidate.strip().strip('"').strip("'").rstrip("/")
        variants: list[str] = [candidate]  # Always try the full path first

        split_markers = [",", " and ", " then ", " to ", " where ", " that ", " for "]
        lowered = candidate.lower()
        for marker in split_markers:
            idx = lowered.find(marker)
            if idx > 2:
                variants.append(candidate[:idx].rstrip(" .;,/"))

        parts = candidate.split("/")
        while len(parts) > 2:
            parts = parts[:-1]
            variants.append("/".join(parts))

        deduped = []
        seen = set()
        for item in variants:
            key = item.lower()
            if key not in seen and item:
                seen.add(key)
                deduped.append(item)
        return deduped
