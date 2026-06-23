"""LLM client wrapper with safe fallbacks for OpenAI.

Provides simple `generate` and `generate_json` helpers.
If `OPENAI_API_KEY` is not set or `openai` isn't installed, falls back to a harmless message.
"""

import os
import json
import re
from typing import Optional, Dict, Any
from pathlib import Path

try:
    import openai
    OPENAI_INSTALLED = True
except Exception:
    openai = None
    OPENAI_INSTALLED = False


class LLMClient:
    def __init__(self, model: Optional[str] = None, temperature: float = 0.0):
        self.model = model or os.getenv('LLM_MODEL', 'gpt-3.5-turbo')
        self.temperature = temperature
        # Try environment first
        self.api_key = os.getenv('OPENAI_API_KEY')

        # If not present, attempt to read from a nearby AI-FACTORY .env file (user provided)
        if not self.api_key:
            candidates = [
                str(Path.home() / 'Documents' / 'GitHub' / 'AI-FACTORY-v2' / '.env'),
                str(Path.cwd().parent / 'AI-FACTORY-v2' / '.env'),
                r'C:\Users\Inaki Senar\Documents\GitHub\AI-FACTORY-v2\.env'
            ]
            for p in candidates:
                try:
                    if os.path.exists(p):
                        self._load_env_file(p)
                        self.api_key = os.getenv('OPENAI_API_KEY')
                        if self.api_key:
                            break
                except Exception:
                    continue

        self.openai_available = OPENAI_INSTALLED and bool(self.api_key)
        if self.openai_available:
            try:
                # for the legacy `openai` module
                if hasattr(openai, 'api_key'):
                    openai.api_key = self.api_key
            except Exception:
                pass

    def _load_env_file(self, path: str) -> None:
        """Carga pares KEY=VALUE desde un archivo .env al `os.environ` sin imprimir valores."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' not in line:
                        continue
                    key, val = line.split('=', 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key and val:
                        # Do not overwrite existing env vars
                        os.environ.setdefault(key, val)
        except Exception as e:
            # Quietly ignore failures to read the external .env
            print(f"Warning: could not load env file {path}: {e}")

    def generate(self, prompt: str, max_tokens: Optional[int] = 1500) -> str:
        if self.openai_available:
            try:
                # Support both legacy and new OpenAI client usage
                if hasattr(openai, 'OpenAI'):
                    client = openai.OpenAI(api_key=self.api_key)
                    resp = client.chat.create(model=self.model, messages=[{"role": "user", "content": prompt}], temperature=self.temperature, max_tokens=max_tokens)
                    content = resp.choices[0].message.content
                else:
                    resp = openai.ChatCompletion.create(
                        model=self.model,
                        messages=[{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": prompt}],
                        temperature=self.temperature,
                        max_tokens=max_tokens,
                    )
                    # Some versions return different shapes
                    choice = resp.choices[0]
                    content = choice.message['content'] if hasattr(choice, 'message') or isinstance(choice, dict) and 'message' in choice else getattr(choice, 'text', '')
                return content
            except Exception as e:
                print(f"LLM client call failed: {e}")

        # Fallback safe response
        if 'json' in prompt.lower() or 'responde' in prompt.lower():
            return json.dumps({"error": "LLM not available. Set OPENAI_API_KEY to enable real responses."})
        return "[LLM unavailable] Install `openai` and set `OPENAI_API_KEY` to enable full functionality."

    def generate_json(self, prompt: str) -> Dict[str, Any]:
        text = self.generate(prompt)
        try:
            return json.loads(text)
        except Exception:
            # try to extract a JSON-like substring
            m = re.search(r'(\{(?:.|\n)*?\}|\[(?:.|\n)*?\])', text, re.S)
            if m:
                try:
                    return json.loads(m.group(1))
                except Exception:
                    pass
            return {"_raw": text}
