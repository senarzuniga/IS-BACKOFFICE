"""OutputGenerator — converts FolderAnalysis into structured output formats."""

from __future__ import annotations

from datetime import datetime

from document_analysis.models import AnalysisOutput, FolderAnalysis, OutputFormat


class OutputGenerator:
    """Generate a formatted :class:`AnalysisOutput` from a :class:`FolderAnalysis`."""

    def generate(self, analysis: FolderAnalysis, output_format: OutputFormat) -> AnalysisOutput:
        _DISPATCH = {
            OutputFormat.SUMMARY: self._summary,
            OutputFormat.EXECUTIVE_SUMMARY: self._executive_summary,
            OutputFormat.REPORT: self._report,
            OutputFormat.PRESENTATION: self._presentation,
            OutputFormat.LIST: self._list,
            OutputFormat.DATABASE_ENTRY: self._database_entry,
            OutputFormat.KNOWLEDGE_GRAPH: self._knowledge_graph,
            OutputFormat.NEW_BRIEF: self._new_brief,
            OutputFormat.COMPARISON: self._comparison,
            OutputFormat.TIMELINE: self._timeline,
            OutputFormat.CLIENT_BRIEF: self._client_brief,
        }
        handler = _DISPATCH.get(output_format, self._summary)
        content, structured = handler(analysis)

        return AnalysisOutput(
            title=f"{output_format.value.replace('_', ' ').title()} — {analysis.folder_path}",
            output_format=output_format,
            content=content,
            structured_data=structured,
            source_analysis=analysis,
            word_count=len(content.split()),
        )

    # ------------------------------------------------------------------
    # Format implementations
    # ------------------------------------------------------------------

    def _summary(self, a: FolderAnalysis) -> tuple[str, dict]:
        lines = [
            "# Document Folder Summary",
            f"**Folder:** {a.folder_path}",
            f"**Analysed:** {a.analyzed_at.strftime('%Y-%m-%d %H:%M')}",
            f"**Documents processed:** {a.stats.supported_files}",
            "",
            "## Overview",
            a.narrative,
            "",
        ]
        if a.cross_themes:
            lines += ["## Key Themes", ", ".join(a.cross_themes), ""]
        if a.gaps:
            lines += ["## Identified Gaps"] + [f"- {g}" for g in a.gaps] + [""]
        if a.contradictions:
            lines += ["## Potential Contradictions"] + [f"- {c}" for c in a.contradictions] + [""]
        content = "\n".join(lines)
        return content, {"themes": a.cross_themes, "gaps": a.gaps}

    def _executive_summary(self, a: FolderAnalysis) -> tuple[str, dict]:
        doc_types = a.stats.files_by_type
        type_str = ", ".join(f"{v} {k.upper()}" for k, v in doc_types.items())
        total_words = sum(d.word_count for d in a.documents if not d.error)

        lines = [
            "# EXECUTIVE SUMMARY",
            f"**Date:** {datetime.now().strftime('%B %d, %Y')}",
            f"**Source:** {a.folder_path}",
            "",
            "## At a Glance",
            f"- **{a.stats.supported_files}** documents analysed ({type_str})",
            f"- **{total_words:,}** total words reviewed",
            f"- **{len(a.relationships)}** cross-document entity relationships identified",
            f"- **{len(a.timeline)}** temporal references extracted",
            "",
            "## Key Findings",
            a.narrative,
            "",
            "## Strategic Themes",
        ]
        for t in a.cross_themes[:5]:
            lines.append(f"- **{t.title()}**")
        lines += ["", "## Recommended Actions"]
        if a.gaps:
            for g in a.gaps:
                lines.append(f"- Address: {g}")
        else:
            lines.append("- No critical gaps identified.")
        content = "\n".join(lines)
        return content, {"word_count": total_words, "themes": a.cross_themes[:5]}

    def _report(self, a: FolderAnalysis) -> tuple[str, dict]:
        lines = [
            "# Document Analysis Report",
            f"_Generated: {a.analyzed_at.strftime('%Y-%m-%d %H:%M')}_",
            "",
            "## 1. Scope",
            f"Folder: `{a.folder_path}`",
            f"Total files discovered: {a.stats.total_files}",
            f"Files successfully parsed: {a.stats.supported_files}",
            f"Parsing errors: {len(a.processing_errors)}",
            "",
            "## 2. Content Overview",
            a.narrative,
            "",
            "## 3. Cross-Document Themes",
        ]
        if a.cross_themes:
            for i, t in enumerate(a.cross_themes, 1):
                lines.append(f"{i}. {t}")
        else:
            lines.append("No shared themes identified.")
        lines += ["", "## 4. Entity Relationships"]
        for rel in a.relationships[:10]:
            lines.append(
                f"- **{rel.entity_a}** ({rel.relationship_type}) across "
                f"{len(rel.source_documents)} document(s)"
            )
        lines += ["", "## 5. Timeline"]
        for ev in a.timeline[:10]:
            lines.append(f"- [{ev.date}] {ev.description[:100]}… ({ev.source_document})")
        lines += ["", "## 6. Gaps & Contradictions"]
        for g in a.gaps:
            lines.append(f"- ⚠️ {g}")
        for c in a.contradictions:
            lines.append(f"- ⚡ {c}")
        content = "\n".join(lines)
        return content, {"relationships": len(a.relationships), "timeline_events": len(a.timeline)}

    def _presentation(self, a: FolderAnalysis) -> tuple[str, dict]:
        total_words = sum(d.word_count for d in a.documents if not d.error)
        doc_types = a.stats.files_by_type
        type_str = ", ".join(f"{v} {k.upper()}" for k, v in doc_types.items())

        slides: list[dict] = []

        # Slide 1 – Title
        slides.append({
            "slide": 1,
            "title": "Document Analysis",
            "bullets": [
                f"Source: {a.folder_path}",
                f"Date: {a.analyzed_at.strftime('%B %d, %Y')}",
                f"{a.stats.supported_files} documents analysed",
            ],
        })

        # Slide 2 – Key Figures
        slides.append({
            "slide": 2,
            "title": "Key Figures",
            "bullets": [
                f"📄 {a.stats.supported_files} documents ({type_str})",
                f"📝 {total_words:,} total words reviewed",
                f"🔗 {len(a.relationships)} cross-document relationships",
                f"📅 {len(a.timeline)} temporal references extracted",
                f"🏷️ {sum(len(d.entities) for d in a.documents)} entities identified",
            ],
        })

        # Slide 3 – Main Themes
        theme_bullets = [f"• {t.title()}" for t in a.cross_themes[:8]]
        if not theme_bullets:
            theme_bullets = ["• No recurring themes identified across documents."]
        slides.append({
            "slide": 3,
            "title": "Main Themes",
            "bullets": theme_bullets,
        })

        # Slide 4 – Key Findings (one sentence per document)
        finding_bullets = []
        for doc in a.documents[:6]:
            if doc.summary and not doc.error:
                finding_bullets.append(f"**{doc.file_name}**: {doc.summary[:120]}…")
        if not finding_bullets:
            finding_bullets = [a.narrative[:400]]
        slides.append({
            "slide": 4,
            "title": "Key Findings",
            "bullets": finding_bullets,
        })

        # Slide 5 – Key Entities
        entities_all = [e for d in a.documents for e in d.entities]
        entity_lines: list[str] = []
        seen: set[str] = set()
        for e in entities_all:
            key = e.text.lower()
            if key not in seen and len(entity_lines) < 8:
                seen.add(key)
                entity_lines.append(f"• **{e.text}** ({e.entity_type.value})")
        slides.append({
            "slide": 5,
            "title": "Key Entities",
            "bullets": entity_lines or ["• No entities extracted."],
        })

        # Slide 6 – Gaps & Next Steps
        next_steps = a.gaps or ["Continue monitoring for new information."]
        slides.append({
            "slide": 6,
            "title": "Gaps & Next Steps",
            "bullets": [f"▶ {g}" for g in next_steps[:6]],
        })

        lines: list[str] = ["# Presentation Outline\n"]
        for s in slides:
            lines.append(f"---\n\n### Slide {s['slide']}: {s['title']}\n")
            for b in s["bullets"]:
                lines.append(f"- {b}")
            lines.append("")

        return "\n".join(lines), {"slides": slides}

    def _client_brief(self, a: FolderAnalysis) -> tuple[str, dict]:
        """Generate a polished, client-ready document brief."""
        total_words = sum(d.word_count for d in a.documents if not d.error)
        doc_types = a.stats.files_by_type
        type_str = ", ".join(f"{v} {k.upper()}" for k, v in doc_types.items())
        date_str = datetime.now().strftime("%B %d, %Y")

        lines = [
            "# CLIENT BRIEF",
            f"**Prepared:** {date_str}",
            f"**Source:** {a.folder_path}",
            f"**Classification:** Confidential",
            "",
            "---",
            "",
            "## 1. SITUATION OVERVIEW",
            a.narrative,
            "",
            f"> *Analysis covers {a.stats.supported_files} document(s) ({type_str}) "
            f"totalling approximately {total_words:,} words.*",
            "",
            "## 2. KEY TOPICS & THEMES",
        ]

        if a.cross_themes:
            for i, theme in enumerate(a.cross_themes[:8], 1):
                lines.append(f"{i}. **{theme.title()}**")
        else:
            lines.append("No recurring themes identified. Documents cover diverse topics.")

        lines += ["", "## 3. KEY ENTITIES & ACTORS"]
        entities_all = [e for d in a.documents for e in d.entities]
        entity_by_type: dict[str, list[str]] = {}
        seen: set[str] = set()
        for e in entities_all:
            key = e.text.lower()
            if key not in seen:
                seen.add(key)
                entity_by_type.setdefault(e.entity_type.value, []).append(e.text)

        for etype, texts in entity_by_type.items():
            lines.append(f"**{etype.title()}:** {', '.join(texts[:6])}")

        if not entity_by_type:
            lines.append("No specific entities extracted.")

        lines += ["", "## 4. DOCUMENT SUMMARIES"]
        for doc in a.documents[:8]:
            if doc.error:
                lines.append(f"- ⚠️ **{doc.file_name}** — parsing error: {doc.error}")
            else:
                summary = doc.summary or "(no summary available)"
                lines.append(f"- 📄 **{doc.file_name}** ({doc.doc_type.value.upper()}, {doc.word_count:,} words)")
                lines.append(f"  {summary[:200]}")
        if len(a.documents) > 8:
            lines.append(f"  _…and {len(a.documents) - 8} more document(s)._")

        lines += ["", "## 5. CROSS-DOCUMENT RELATIONSHIPS"]
        if a.relationships:
            for rel in a.relationships[:8]:
                lines.append(
                    f"- **{rel.entity_a}** appears in {len(rel.source_documents)} document(s): "
                    f"{', '.join(rel.source_documents[:3])}"
                )
        else:
            lines.append("No significant cross-document relationships identified.")

        lines += ["", "## 6. TIMELINE OF KEY EVENTS"]
        if a.timeline:
            for ev in a.timeline[:10]:
                lines.append(f"- **{ev.date}** — {ev.description[:120]} _(from {ev.source_document})_")
        else:
            lines.append("No temporal events extracted.")

        lines += ["", "## 7. IDENTIFIED GAPS"]
        if a.gaps:
            for g in a.gaps:
                lines.append(f"- ⚠️ {g}")
        else:
            lines.append("- No critical information gaps identified.")

        lines += ["", "## 8. RECOMMENDATIONS & NEXT STEPS"]
        if a.gaps:
            for g in a.gaps:
                lines.append(f"- Address: {g}")
        if a.contradictions:
            for c in a.contradictions:
                lines.append(f"- Verify: {c}")
        if not a.gaps and not a.contradictions:
            lines.append("- Document collection appears complete. Consider creating a knowledge graph for deeper analysis.")
            lines.append("- Review individual summaries with subject-matter experts.")

        lines += [
            "",
            "---",
            f"*Brief generated automatically on {date_str}. Review before client distribution.*",
        ]

        content = "\n".join(lines)
        return content, {
            "themes": a.cross_themes,
            "entity_types": list(entity_by_type.keys()),
            "doc_count": len(a.documents),
            "word_count": total_words,
        }

    def _list(self, a: FolderAnalysis) -> tuple[str, dict]:
        lines = ["# Document List\n"]
        items = []
        for doc in a.documents:
            status = "✅" if not doc.error else "❌"
            line = (
                f"{status} **{doc.file_name}** ({doc.doc_type.value.upper()}) — "
                f"{doc.word_count:,} words, {len(doc.entities)} entities"
            )
            lines.append(line)
            items.append({"name": doc.file_name, "type": doc.doc_type.value, "words": doc.word_count})
        return "\n".join(lines), {"documents": items}

    def _database_entry(self, a: FolderAnalysis) -> tuple[str, dict]:
        records = []
        for doc in a.documents:
            records.append({
                "file_name": doc.file_name,
                "doc_type": doc.doc_type.value,
                "word_count": doc.word_count,
                "page_count": doc.page_count,
                "entity_count": len(doc.entities),
                "topics": doc.topics[:5],
                "summary": doc.summary[:200],
                "error": doc.error,
            })
        import json
        content = json.dumps(records, indent=2, ensure_ascii=False, default=str)
        return content, {"records": records}

    def _knowledge_graph(self, a: FolderAnalysis) -> tuple[str, dict]:
        nodes = set()
        edges = []
        for rel in a.relationships:
            nodes.add(rel.entity_a)
            for doc_name in rel.source_documents:
                nodes.add(doc_name)
                edges.append({"from": rel.entity_a, "to": doc_name, "type": rel.relationship_type, "weight": rel.strength})

        lines = ["# Knowledge Graph Export", "", "## Nodes"]
        for n in sorted(nodes):
            lines.append(f"- {n}")
        lines += ["", "## Edges (entity → document)"]
        for e in edges[:30]:
            lines.append(f"- **{e['from']}** --[{e['type']}]--> {e['to']} (weight: {e['weight']:.2f})")
        content = "\n".join(lines)
        return content, {"nodes": list(nodes), "edges": edges}

    def _new_brief(self, a: FolderAnalysis) -> tuple[str, dict]:
        lines = [
            "# Intelligence Brief",
            f"_Compiled: {datetime.now().strftime('%B %d, %Y')}_",
            "",
            "**SUBJECT:** Document Folder Analysis",
            f"**SOURCE:** {a.folder_path}",
            "",
            "## SITUATION",
            a.narrative,
            "",
            "## KEY ENTITIES",
        ]
        for rel in a.relationships[:8]:
            lines.append(f"- {rel.entity_a} (found in {len(rel.source_documents)} docs)")
        lines += ["", "## ASSESSMENT"]
        if a.contradictions:
            for c in a.contradictions:
                lines.append(f"- {c}")
        else:
            lines.append("- No significant contradictions detected.")
        lines += ["", "## RECOMMENDED FOLLOW-UP"]
        for g in a.gaps or ["Continue monitoring for new information."]:
            lines.append(f"- {g}")
        content = "\n".join(lines)
        return content, {}

    def _comparison(self, a: FolderAnalysis) -> tuple[str, dict]:
        lines = ["# Document Comparison\n", "| Document | Type | Words | Entities | Topics |", "|---|---|---|---|---|"]
        rows = []
        for doc in a.documents:
            topics = ", ".join(doc.topics[:3])
            lines.append(f"| {doc.file_name} | {doc.doc_type.value.upper()} | {doc.word_count:,} | {len(doc.entities)} | {topics} |")
            rows.append({"file": doc.file_name, "type": doc.doc_type.value, "words": doc.word_count, "entities": len(doc.entities)})
        content = "\n".join(lines)
        return content, {"rows": rows}

    def _timeline(self, a: FolderAnalysis) -> tuple[str, dict]:
        lines = ["# Timeline of Events\n"]
        events = []
        for ev in a.timeline:
            lines.append(f"**{ev.date}** — {ev.description[:150]} _(source: {ev.source_document})_")
            events.append({"date": ev.date, "description": ev.description, "source": ev.source_document})
        if not events:
            lines.append("_No temporal events extracted._")
        content = "\n".join(lines)
        return content, {"events": events}
