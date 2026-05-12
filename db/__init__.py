"""Supabase database layer for IS-BACKOFFICE."""
from .client import get_supabase_client, SupabaseClient

__all__ = ["get_supabase_client", "SupabaseClient"]
