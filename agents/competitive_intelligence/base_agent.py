from dotenv import load_dotenv
import os
import logging
import json
from typing import List, Dict, Any, Optional

load_dotenv()

try:
    import openai
except Exception:
    openai = None

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

if OPENAI_API_KEY and openai:
    openai.api_key = OPENAI_API_KEY

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class BaseAgent:
    """Minimal base agent that wraps OpenAI calls and provides safe fallbacks."""

    def __init__(self, model: Optional[str] = None):
        self.model = model or OPENAI_MODEL

    def call_llm(self, messages: List[Dict[str, str]], temperature: float = 0.0, max_tokens: int = 1200) -> str:
        """Call LLM and return raw text. If OpenAI is not configured, returns a fallback string."""
        if not (OPENAI_API_KEY and openai):
            logger.warning("OPENAI not configured — running in demo fallback mode")
            # fallback: return concatenated user messages
            return "\n\n".join(m.get("content", "") for m in messages if m.get("role") == "user")

        # Support both old and new openai client shapes
        try:
            # new API: openai.chat.completions.create
            if hasattr(openai, "chat") and hasattr(openai.chat, "completions"):
                resp = openai.chat.completions.create(model=self.model, messages=messages, temperature=temperature, max_tokens=max_tokens)
                return resp["choices"][0]["message"]["content"]
            # older API compatibility layer
            if hasattr(openai, "ChatCompletion"):
                resp = openai.ChatCompletion.create(model=self.model, messages=messages, temperature=temperature, max_tokens=max_tokens)
                return resp["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning("OpenAI call failed: %s", e)
            # fallback to concatenated user messages
            return "\n\n".join(m.get("content", "") for m in messages if m.get("role") == "user")

    def call_llm_json(self, messages: List[Dict[str, str]], temperature: float = 0.0, max_tokens: int = 1200) -> Any:
        text = self.call_llm(messages, temperature=temperature, max_tokens=max_tokens)
        try:
            return json.loads(text)
        except Exception:
            # try to extract JSON substring
            import re

            m = re.search(r"\{[\s\S]*\}", text)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception:
                    pass
            return {"_raw": text}
