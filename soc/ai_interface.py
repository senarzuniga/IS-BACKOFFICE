from __future__ import annotations

import os
import re
from typing import Optional


def _simple_extractive_summary(text: str, max_chars: int = 800) -> str:
    if not text:
        return ""
    # split by paragraphs or sentences
    parts = re.split(r'\n{2,}|\.[\s\n]+', text)
    parts = [p.strip() for p in parts if p.strip()]
    out = ' '.join(parts[:3])
    return out[:max_chars]


def summarize(text: str, use_openai: bool = False, max_chars: int = 800) -> str:
    """Return a short summary for the given text.

    If `use_openai` is True and an `OPENAI_API_KEY` is present, this will
    attempt to call OpenAI. By default the function uses a safe local
    extractive summarizer so the system works offline.
    """
    if use_openai and os.environ.get('OPENAI_API_KEY'):
        try:
            import openai

            openai.api_key = os.environ.get('OPENAI_API_KEY')
            prompt = f"Summarize in one short paragraph the following text:\n\n{text[:3000]}"
            resp = openai.Completion.create(engine='text-davinci-003', prompt=prompt, max_tokens=200)
            return resp.choices[0].text.strip()
        except Exception:
            # fallback
            pass

    return _simple_extractive_summary(text, max_chars=max_chars)
