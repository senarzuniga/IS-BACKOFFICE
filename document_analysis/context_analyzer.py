"""ContextAnalyzer — cross-document analysis: themes, relationships, timeline, narrative."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any

from document_analysis.models import (
    CrossReference,
    DocumentInfo,
    FolderAnalysis,
    FolderStats,
    TimelineEvent,
)


class ContextAnalyzer:
    """Analyse a collection of :class:`DocumentInfo` objects to find cross-document patterns."""

    def analyze_folder(
        self,
        documents: list[DocumentInfo],
        folder_path: str,
        stats: FolderStats,
    ) -> FolderAnalysis:
        """Return a :class:`FolderAnalysis` from a list of parsed documents."""
        errors = [f"{d.file_name}: {d.error}" for d in documents if d.error]
        valid_docs = [d for d in documents if not d.error and d.raw_text.strip()]

        cross_themes = self._find_cross_themes(valid_docs)
        relationships = self._find_relationships(valid_docs)
        timeline = self._build_timeline(valid_docs)
        narrative = self._generate_narrative(valid_docs, cross_themes)
        gaps = self._detect_gaps(valid_docs)
        contradictions = self._detect_contradictions(valid_docs)

        return FolderAnalysis(
            folder_path=folder_path,
            stats=stats,
            documents=documents,
            cross_themes=cross_themes,
            relationships=relationships,
            timeline=timeline,
            narrative=narrative,
            gaps=gaps,
            contradictions=contradictions,
            processing_errors=errors,
        )

    # ------------------------------------------------------------------
    # Analysis sub-routines
    # ------------------------------------------------------------------

    def _find_cross_themes(self, docs: list[DocumentInfo], top_n: int = 15) -> list[str]:
        """Return the most common topics shared across multiple documents."""
        topic_doc_count: dict[str, int] = defaultdict(int)
        for doc in docs:
            for topic in set(doc.topics):
                topic_doc_count[topic] += 1

        # Keep topics that appear in at least 2 documents (or all, if fewer docs)
        min_docs = min(2, len(docs))
        shared = {t: c for t, c in topic_doc_count.items() if c >= min_docs}
        top = sorted(shared.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return [t for t, _ in top]

    def _find_relationships(self, docs: list[DocumentInfo]) -> list[CrossReference]:
        """Find entity mentions shared across documents and create cross-references."""
        # Build entity → document mapping
        entity_docs: dict[str, list[str]] = defaultdict(list)
        for doc in docs:
            for ent in doc.entities:
                key = ent.text.lower().strip()
                if len(key) > 2 and doc.file_name not in entity_docs[key]:
                    entity_docs[key].append(doc.file_name)

        refs: list[CrossReference] = []
        for entity, doc_names in entity_docs.items():
            if len(doc_names) >= 2:
                refs.append(
                    CrossReference(
                        entity_a=entity,
                        entity_b="(multiple documents)",
                        relationship_type="co-mentioned",
                        strength=min(1.0, len(doc_names) / len(docs)),
                        source_documents=doc_names,
                    )
                )
        refs.sort(key=lambda r: r.strength, reverse=True)
        return refs[:50]  # cap at 50

    def _build_timeline(self, docs: list[DocumentInfo]) -> list[TimelineEvent]:
        """Extract date-anchored events from entity lists."""
        events: list[TimelineEvent] = []
        for doc in docs:
            for ent in doc.entities:
                from document_analysis.models import EntityType

                if ent.entity_type == EntityType.DATE and ent.context.strip():
                    events.append(
                        TimelineEvent(
                            date=ent.text,
                            description=ent.context.strip()[:200],
                            source_document=doc.file_name,
                            confidence=ent.confidence,
                        )
                    )
        return events[:100]

    def _generate_narrative(self, docs: list[DocumentInfo], themes: list[str]) -> str:
        """Produce a short textual narrative about the folder contents."""
        if not docs:
            return "No documents were successfully parsed."

        doc_count = len(docs)
        total_words = sum(d.word_count for d in docs)
        theme_summary = ", ".join(themes[:8]) if themes else "various topics"

        doc_types: Counter = Counter(d.doc_type.value for d in docs)
        type_summary = ", ".join(f"{v} {k.upper()}" for k, v in doc_types.most_common(4))

        return (
            f"This folder contains {doc_count} document(s) ({type_summary}) "
            f"with approximately {total_words:,} total words. "
            f"Key cross-document themes include: {theme_summary}. "
            f"The collection covers {len(set(e.entity_type.value for d in docs for e in d.entities))} "
            f"distinct entity categories."
        )

    def _detect_gaps(self, docs: list[DocumentInfo]) -> list[str]:
        """Identify potential information gaps based on common business document patterns."""
        gaps: list[str] = []
        all_topics = set(t for d in docs for t in d.topics)

        _EXPECTED_PAIRS = [
            ({"revenue", "sales", "income"}, "financial figures (no financial data found)"),
            ({"date", "year", "quarter"}, "time references (documents may lack temporal context)"),
            ({"client", "customer", "account"}, "client/customer references"),
            ({"contact", "email", "phone"}, "contact information"),
        ]
        for keywords, description in _EXPECTED_PAIRS:
            if not keywords.intersection(all_topics):
                gaps.append(f"Missing: {description}")

        if not docs:
            gaps.append("No documents could be parsed.")

        return gaps

    def _detect_contradictions(self, docs: list[DocumentInfo]) -> list[str]:
        """Detect potential contradictions (money amounts, dates) across documents."""
        contradictions: list[str] = []
        from document_analysis.models import EntityType

        # Money values
        money_by_doc: dict[str, list[str]] = {}
        for doc in docs:
            amounts = [e.text for e in doc.entities if e.entity_type == EntityType.MONEY]
            if amounts:
                money_by_doc[doc.file_name] = amounts

        if len(money_by_doc) >= 2:
            all_amounts = set(v for vals in money_by_doc.values() for v in vals)
            if len(all_amounts) > len(money_by_doc):
                contradictions.append(
                    f"Different monetary figures appear across {len(money_by_doc)} documents — "
                    "verify consistency."
                )

        return contradictions
