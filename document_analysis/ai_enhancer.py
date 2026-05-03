"""AIEnhancer — optional OpenAI-powered text enhancement with graceful fallback."""

from __future__ import annotations

import os
from typing import Any

from document_analysis.models import AnalysisOutput, FolderAnalysis


class AIEnhancer:
    """Enhance analysis output using OpenAI GPT when configured, otherwise no-op."""

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini") -> None:
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._model = model
        self._available = self._check_availability()

    @property
    def is_available(self) -> bool:
        return self._available

    def enhance_output(self, output: AnalysisOutput) -> AnalysisOutput:
        """Rewrite the output content using GPT for better prose. Returns as-is if unavailable."""
        if not self._available:
            return output
        try:
            enhanced = self._call_openai(
                system=(
                    "You are a business analyst. Rewrite the following document analysis output "
                    "to be clear, professional, and concise. Preserve all factual content. "
                    "Return only the rewritten text, no commentary."
                ),
                user=output.content[:8_000],
            )
            output.content = enhanced
            output.ai_enhanced = True
        except Exception:  # noqa: BLE001
            pass  # Fall back silently to original content
        return output

    def generate_insights(self, analysis: FolderAnalysis) -> str:
        """Return AI-generated strategic insights about the folder analysis."""
        if not self._available:
            return _fallback_insights(analysis)
        try:
            prompt = (
                f"Given the following document folder analysis:\n\n"
                f"Narrative: {analysis.narrative}\n"
                f"Themes: {', '.join(analysis.cross_themes[:10])}\n"
                f"Gaps: {', '.join(analysis.gaps)}\n\n"
                "Provide 3-5 concise strategic insights and recommended actions."
            )
            return self._call_openai(
                system="You are a senior business intelligence analyst.",
                user=prompt,
            )
        except Exception:  # noqa: BLE001
            return _fallback_insights(analysis)

    def summarize_document(self, raw_text: str, max_words: int = 150) -> str:
        """Summarize a single document's text using GPT, or truncate if unavailable."""
        if not self._available or not raw_text.strip():
            return _truncate_summary(raw_text, max_words)
        try:
            return self._call_openai(
                system=f"Summarize the following text in under {max_words} words.",
                user=raw_text[:6_000],
            )
        except Exception:  # noqa: BLE001
            return _truncate_summary(raw_text, max_words)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _check_availability(self) -> bool:
        if not self._api_key:
            return False
        try:
            import openai  # noqa: F401

            return True
        except ImportError:
            return False

    def _call_openai(self, system: str, user: str) -> str:
        import openai

        client = openai.OpenAI(api_key=self._api_key)
        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=1500,
            temperature=0.3,
        )
        return response.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# Fallbacks
# ---------------------------------------------------------------------------

def _fallback_insights(analysis: FolderAnalysis) -> str:
    insights = []
    if analysis.cross_themes:
        insights.append(f"The dominant themes ({', '.join(analysis.cross_themes[:3])}) suggest a focused collection.")
    if analysis.gaps:
        insights.append(f"Address the following gaps to improve completeness: {'; '.join(analysis.gaps[:2])}.")
    if analysis.relationships:
        insights.append(
            f"{len(analysis.relationships)} cross-document relationships identified — "
            "consider linking these in your knowledge graph."
        )
    if not insights:
        return "No AI insights available. Configure OPENAI_API_KEY to enable AI enhancement."
    return "\n".join(f"• {i}" for i in insights)


def _truncate_summary(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "…"
