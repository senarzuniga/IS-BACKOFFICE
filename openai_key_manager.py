from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Any

_EXTERNAL_MODULE_PATH = Path(r"C:\Users\Inaki Senar\Documents\GitHub\AI-Factory-v2\openai_key_manager.py")


def _load_external_module() -> Any | None:
    """Load AI-Factory key manager module without importing this module recursively."""
    if not _EXTERNAL_MODULE_PATH.exists():
        return None
    spec = importlib.util.spec_from_file_location("ai_factory_openai_key_manager", _EXTERNAL_MODULE_PATH)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OpenAIMasterKeyManager:
    """Minimal local fallback manager for OPENAI_API_KEY resolution."""

    def __init__(self, env_var: str = "OPENAI_API_KEY") -> None:
        self.env_var = env_var

    def get_api_key(self) -> str:
        api_key = os.environ.get(self.env_var, "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        return api_key

    def setup_env(self) -> str:
        api_key = self.get_api_key()
        os.environ[self.env_var] = api_key
        return api_key


_external = _load_external_module()
if _external is not None:
    OpenAIMasterKeyManager = getattr(_external, "OpenAIMasterKeyManager", OpenAIMasterKeyManager)


def get_openai_manager() -> OpenAIMasterKeyManager:
    if _external is not None and hasattr(_external, "get_openai_manager"):
        return _external.get_openai_manager()
    return OpenAIMasterKeyManager()


def get_openai_api_key() -> str:
    if _external is not None and hasattr(_external, "get_openai_api_key"):
        return _external.get_openai_api_key()
    return get_openai_manager().get_api_key()


def setup_openai_env() -> str:
    if _external is not None and hasattr(_external, "setup_openai_env"):
        return _external.setup_openai_env()
    return get_openai_manager().setup_env()


__all__ = ["OpenAIMasterKeyManager", "get_openai_api_key", "get_openai_manager", "setup_openai_env"]
