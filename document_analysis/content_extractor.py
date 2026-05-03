"""ContentExtractor — extracts entities, topics, and summaries from raw text."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from document_analysis.models import DocumentInfo, EntityType, ExtractedEntity


# ---------------------------------------------------------------------------
# Regex-based entity patterns (used when spaCy is unavailable)
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE)
_PHONE_RE = re.compile(r"\+?\d[\d\s\-().]{8,}\d")
_DATE_RE = re.compile(
    r"\b(?:\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}"
    r"|\d{4}[/\-]\d{1,2}[/\-]\d{1,2}"
    r"|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}"
    r"|Q[1-4]\s+\d{4})\b",
    re.IGNORECASE,
)
_MONEY_RE = re.compile(r"(?:USD|EUR|GBP|€|\$|£)\s*[\d,]+(?:\.\d{1,2})?|\b[\d,]+(?:\.\d{1,2})?\s*(?:USD|EUR|GBP)\b")
_ORG_SUFFIXES = re.compile(
    r"\b[A-Z][A-Za-z&\s]{1,40}"
    r"(?:Inc\.?|Corp\.?|LLC\.?|Ltd\.?|GmbH|S\.A\.?|Co\.?|Group|Holdings|Partners|Associates|Ventures)\b"
)
_CAPITALIZED_SEQUENCE = re.compile(r"\b(?:[A-Z][a-z]{1,20}\s){1,4}[A-Z][a-z]{1,20}\b")


# Common English stop-words for topic extraction (no external dependency)
_STOP_WORDS = frozenset(
    "the a an and or but in on at to of for with is are was were be been being have has had "
    "do does did will would could should may might shall must not no nor so yet both either "
    "as by from into than that this those these through which who whom whose when where how "
    "all any both each few more most other some such no only same than too very can just "
    "about above after before between during under over within without against between among "
    "i we you he she it they them their our your my his her its us me him".split()
)


class ContentExtractor:
    """Extract entities, topics, and summaries from a :class:`DocumentInfo`.

    Uses spaCy when available, falling back to pure-Python regex patterns.
    """

    def __init__(self, use_spacy: bool = True) -> None:
        self._nlp = None
        if use_spacy:
            try:
                import spacy

                self._nlp = spacy.load("en_core_web_sm")
            except Exception:  # noqa: BLE001
                self._nlp = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def enrich(self, doc_info: DocumentInfo) -> DocumentInfo:
        """Add entities, topics, and summary to a :class:`DocumentInfo` in place."""
        text = doc_info.raw_text or ""
        if not text.strip():
            return doc_info
        doc_info.entities = self.extract_entities(text, source_doc=doc_info.file_name)
        doc_info.topics = self.extract_topics(text)
        doc_info.summary = self.generate_summary(text)
        return doc_info

    def extract_entities(self, text: str, source_doc: str = "") -> list[ExtractedEntity]:
        if self._nlp is not None:
            return self._extract_with_spacy(text, source_doc)
        return self._extract_with_regex(text, source_doc)

    def extract_topics(self, text: str, top_n: int = 10) -> list[str]:
        """Return the *top_n* most frequent meaningful words as topic keywords."""
        words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
        filtered = [w for w in words if w not in _STOP_WORDS]
        counts = Counter(filtered)
        return [word for word, _ in counts.most_common(top_n)]

    def generate_summary(self, text: str, max_sentences: int = 5) -> str:
        """Return a simple extractive summary (top scored sentences)."""
        sentences = _split_sentences(text)
        if not sentences:
            return ""
        if len(sentences) <= max_sentences:
            return " ".join(sentences)

        # Score by keyword density
        keywords = set(self.extract_topics(text, top_n=20))
        scored = []
        for idx, sent in enumerate(sentences):
            words = re.findall(r"\b[a-zA-Z]{3,}\b", sent.lower())
            score = sum(1 for w in words if w in keywords)
            # Prefer earlier sentences slightly
            score += max(0, 10 - idx) * 0.1
            scored.append((score, idx, sent))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = sorted(scored[:max_sentences], key=lambda x: x[1])
        return " ".join(s for _, _, s in top)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_with_spacy(self, text: str, source_doc: str) -> list[ExtractedEntity]:
        _SPACY_TYPE_MAP = {
            "PERSON": EntityType.PERSON,
            "ORG": EntityType.ORGANIZATION,
            "GPE": EntityType.LOCATION,
            "LOC": EntityType.LOCATION,
            "DATE": EntityType.DATE,
            "TIME": EntityType.DATE,
            "MONEY": EntityType.MONEY,
            "PRODUCT": EntityType.PRODUCT,
        }
        doc = self._nlp(text[:500_000])  # spaCy has a max limit
        seen: set[tuple[str, str]] = set()
        entities: list[ExtractedEntity] = []
        for ent in doc.ents:
            etype = _SPACY_TYPE_MAP.get(ent.label_, EntityType.OTHER)
            key = (ent.text.strip(), etype.value)
            if key in seen:
                continue
            seen.add(key)
            context = text[max(0, ent.start_char - 60): ent.end_char + 60]
            entities.append(
                ExtractedEntity(
                    text=ent.text.strip(),
                    entity_type=etype,
                    confidence=0.9,
                    source_document=source_doc,
                    context=context,
                )
            )
        return entities

    def _extract_with_regex(self, text: str, source_doc: str) -> list[ExtractedEntity]:
        entities: list[ExtractedEntity] = []
        seen: set[str] = set()

        def _add(txt: str, etype: EntityType, conf: float) -> None:
            key = txt.strip().lower()
            if key and key not in seen:
                seen.add(key)
                entities.append(
                    ExtractedEntity(
                        text=txt.strip(),
                        entity_type=etype,
                        confidence=conf,
                        source_document=source_doc,
                    )
                )

        for m in _DATE_RE.finditer(text):
            _add(m.group(), EntityType.DATE, 0.85)
        for m in _MONEY_RE.finditer(text):
            _add(m.group(), EntityType.MONEY, 0.85)
        for m in _ORG_SUFFIXES.finditer(text):
            _add(m.group(), EntityType.ORGANIZATION, 0.7)
        for m in _CAPITALIZED_SEQUENCE.finditer(text):
            _add(m.group(), EntityType.PERSON, 0.5)

        return entities


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if len(s.strip()) > 30]
