"""Supabase client singleton for IS-BACKOFFICE.

Configure via environment variables:
    SUPABASE_URL             — Project URL (https://<id>.supabase.co)
    SUPABASE_SERVICE_ROLE_KEY — Service role key (bypasses RLS; server-side only)
    SUPABASE_ANON_KEY        — Anon/public key (for client-side or read-only paths)

The service role key is preferred for seeding and server-side operations.
The anon key is used as fallback for read-only access.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

try:
    from supabase import create_client, Client as _SupabaseSDKClient
    _SUPABASE_AVAILABLE = True
except ImportError:
    _SUPABASE_AVAILABLE = False
    _SupabaseSDKClient = object  # type: ignore


class SupabaseClient:
    """Thin wrapper around the Supabase Python SDK client."""

    def __init__(self, url: str, key: str) -> None:
        if not _SUPABASE_AVAILABLE:
            raise RuntimeError(
                "supabase package is not installed. "
                "Run: pip install supabase>=2.10.0"
            )
        self._client: _SupabaseSDKClient = create_client(url, key)

    @property
    def client(self) -> "_SupabaseSDKClient":
        """Return the raw Supabase SDK client for direct table operations."""
        return self._client

    def table(self, name: str):
        """Shortcut: client.table(name)."""
        return self._client.table(name)

    def is_connected(self) -> bool:
        """Quick connectivity check — tries to read 1 row from a known table."""
        try:
            self._client.table("ingecart_company").select("id").limit(1).execute()
            return True
        except Exception:
            return False


@lru_cache(maxsize=1)
def get_supabase_client() -> Optional[SupabaseClient]:
    """Return a cached SupabaseClient instance, or None if not configured.

    Priority:
        1. SUPABASE_SERVICE_ROLE_KEY (for server-side / seeding)
        2. SUPABASE_ANON_KEY (for read-only / public access)
    """
    url: Optional[str] = os.environ.get("SUPABASE_URL")
    if not url:
        return None

    key: Optional[str] = (
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        or os.environ.get("SUPABASE_ANON_KEY")
    )
    if not key:
        return None

    if not _SUPABASE_AVAILABLE:
        return None

    return SupabaseClient(url=url, key=key)
