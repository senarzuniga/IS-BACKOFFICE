"""Database integration package for backoffice enhancements."""

from .supabase_client import SupabaseBackofficeClient, supabase_db

__all__ = ["SupabaseBackofficeClient", "supabase_db"]
