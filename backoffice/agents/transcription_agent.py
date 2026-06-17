"""Simple transcription agent using OpenAI Audio + Chat completions.

Attempts to transcribe uploaded audio via OpenAI (whisper-1) and
provides helper functions to summarise or post-process the text.
This module is intentionally lightweight and defensive about API
variations across OpenAI client versions.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

try:
    import openai
except Exception:  # pragma: no cover - runtime optional
    openai = None


class TranscriptionAgent:
    def __init__(self, openai_api_key: Optional[str] = None) -> None:
        self.key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        if openai and self.key:
            try:
                openai.api_key = self.key
            except Exception:
                # Some environments set the key via env only
                pass

    def _check_client(self) -> None:
        if openai is None:
            raise RuntimeError("openai package is not installed")
        if not self.key:
            raise RuntimeError("OPENAI_API_KEY not configured")

    def transcribe_file(self, file_path: str, language: str = "en") -> Dict[str, Any]:
        """Transcribe an audio file. Returns a dict with keys `text` and
        optionally `raw` containing the original API response.
        """
        self._check_client()

        lang = "es" if str(language).lower().startswith("es") else "en"

        with open(file_path, "rb") as fh:
            # Try modern helper if available
            try:
                if hasattr(openai, "Audio") and hasattr(openai.Audio, "transcribe"):
                    resp = openai.Audio.transcribe("whisper-1", fh, language=lang)
                    # resp is usually a dict-like or object with .text
                    text = None
                    try:
                        text = resp.get("text") if isinstance(resp, dict) else getattr(resp, "text", None)
                    except Exception:
                        text = str(resp)
                    return {"text": text, "raw": resp}

                # Fallback older API paths
                if hasattr(openai, "Audio") and hasattr(openai.Audio, "transcriptions"):
                    resp = openai.Audio.transcriptions.create(model="whisper-1", file=fh, language=lang)
                    return {"text": resp.get("text") if isinstance(resp, dict) else getattr(resp, "text", None), "raw": resp}

                # Final fallback: try the top-level transcription endpoint shape
                if hasattr(openai, "Transcription"):
                    resp = openai.Transcription.create(model="whisper-1", file=fh, language=lang)
                    return {"text": resp.get("text") if isinstance(resp, dict) else getattr(resp, "text", None), "raw": resp}

            except Exception as exc:  # pragma: no cover - runtime integration
                raise RuntimeError(f"Transcription failed: {exc}")

        raise RuntimeError("Unable to call OpenAI transcription API with current client")

    def summarise_text(self, text: str, language: str = "en") -> str:
        """Produce a concise executive summary using the ChatCompletion API.

        Falls back to Completion API if ChatCompletion is unavailable.
        """
        self._check_client()

        lang_label = "English" if str(language).lower().startswith("en") else "Spanish"
        prompt = (
            f"You are a helpful assistant that produces concise executive summaries. "
            f"Summarise the following transcription in {lang_label} as 3–6 bullet points, "
            "preserve named entities and main actions. Keep it short.\n\nTranscription:\n" + text
        )

        try:
            if hasattr(openai, "ChatCompletion"):
                resp = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                )
                choice = resp["choices"][0]
                out = choice.get("message", {}).get("content") if isinstance(choice, dict) else None
                if not out:
                    out = choice.get("text") if isinstance(choice, dict) else str(choice)
                return out.strip()

            # Fallback to Completion API
            resp = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=400, temperature=0.2)
            return resp.get("choices", [])[0].get("text", "").strip()
        except Exception as exc:  # pragma: no cover - runtime integration
            raise RuntimeError(f"Summarisation failed: {exc}")


__all__ = ["TranscriptionAgent"]
