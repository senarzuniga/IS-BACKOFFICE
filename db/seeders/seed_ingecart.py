"""Ingecart data seeder — loads all available Ingecart intelligence into Supabase.

Usage:
    python db/seeders/seed_ingecart.py
    python db/seeders/seed_ingecart.py --dry-run
    python db/seeders/seed_ingecart.py --source company
    python db/seeders/seed_ingecart.py --source products
    python db/seeders/seed_ingecart.py --source events
    python db/seeders/seed_ingecart.py --source documents
    python db/seeders/seed_ingecart.py --source market_intelligence

Environment variables required:
    SUPABASE_URL              — https://<project>.supabase.co
    SUPABASE_SERVICE_ROLE_KEY — Service role key (full write access)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import date
from pathlib import Path

# Allow running from repo root or from this file's directory
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

from db.client import get_supabase_client  # noqa: E402

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------
_RESEARCH_DIR = _REPO_ROOT / "research" / "ingecart"
_INFORMES_DIR = _REPO_ROOT / "informes"
_MARKETING_KIT_DIR = _REPO_ROOT / "ingecart-marketing-kit"


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _checksum(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _load_json(path: Path) -> dict | list:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _read_text(path: Path) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _word_count(text: str) -> int:
    return len(text.split())


def _upsert(client, table: str, rows: list[dict], conflict_col: str | None = None,
            dry_run: bool = False) -> int:
    """Upsert rows into a Supabase table. Returns number of rows processed."""
    if not rows:
        return 0
    if dry_run:
        print(f"  [DRY-RUN] Would upsert {len(rows)} row(s) into '{table}'")
        return len(rows)
    kwargs = {}
    if conflict_col:
        kwargs["on_conflict"] = conflict_col
    client.table(table).upsert(rows, **kwargs).execute()
    print(f"  ✓ Upserted {len(rows)} row(s) into '{table}'")
    return len(rows)


# ---------------------------------------------------------------------------
# Seed: Company Profile
# ---------------------------------------------------------------------------

def seed_company(client, dry_run: bool = False) -> None:
    print("\n[Company Profile]")
    profile_path = _RESEARCH_DIR / "company_profile" / "ingecart_company_profile.json"
    if not profile_path.exists():
        print("  ⚠ Company profile JSON not found, skipping.")
        return
    data = _load_json(profile_path)
    row = {
        "legal_name": data.get("legal_name", "Ingecart S.L."),
        "trade_name": data.get("company", "Ingecart"),
        "industry": data.get("industry"),
        "sector": data.get("industry"),
        "country_primary": data.get("geography", {}).get("primary", "Spain"),
        "geography": data.get("geography"),
        "currency": data.get("currency", "EUR"),
        "languages": data.get("languages"),
        "strengths": data.get("strengths"),
        "growth_vectors": data.get("growth_vectors"),
        "tech_appetite": data.get("technology_appetite"),
        "profile_version": data.get("profile_version", "1.0"),
        "updated_at": "now()",
    }
    _upsert(client, "ingecart_company", [row], dry_run=dry_run)


# ---------------------------------------------------------------------------
# Seed: Products
# ---------------------------------------------------------------------------

def seed_products(client, dry_run: bool = False) -> None:
    print("\n[Products]")
    products_path = _RESEARCH_DIR / "products" / "ingecart_products.json"
    if not products_path.exists():
        print("  ⚠ Products JSON not found, skipping.")
        return
    items: list[dict] = _load_json(products_path)
    rows = []
    for item in items:
        rows.append({
            "product_code": item.get("product_id"),
            "name": item.get("name"),
            "category": item.get("category"),
            "subcategory": item.get("subcategory"),
            "description": item.get("description"),
            "vendor": item.get("vendor"),
            "market_segments": item.get("market_segment"),
            "currency": item.get("currency", "EUR"),
            "technology_integration_candidate": item.get("technology_integration_candidate", False),
            "ai_agent_fit": item.get("ai_agent_fit"),
            "lifecycle_stage": "active",
            "updated_at": "now()",
        })
    _upsert(client, "ingecart_products", rows, conflict_col="product_code", dry_run=dry_run)


# ---------------------------------------------------------------------------
# Seed: Events
# ---------------------------------------------------------------------------

def seed_events(client, dry_run: bool = False) -> None:
    print("\n[Events]")
    events_path = _RESEARCH_DIR / "events" / "ingecart_events.json"
    if not events_path.exists():
        print("  ⚠ Events JSON not found, skipping.")
        return
    items: list[dict] = _load_json(events_path)
    rows = []
    for item in items:
        rows.append({
            "event_code": item.get("event_id"),
            "name": item.get("name"),
            "event_type": item.get("type"),
            "sector": item.get("sector"),
            "location_city": item.get("location", {}).get("city"),
            "location_country": item.get("location", {}).get("country"),
            "event_year": item.get("year"),
            "date_notes": item.get("date_notes"),
            "scale": item.get("scale"),
            "ingecart_role": item.get("ingecart_role"),
            "iar_role": item.get("iar_role"),
            "strategic_report": item.get("strategic_report"),
            "audience_segments": item.get("audience_segments"),
            "dominant_trends": item.get("dominant_trends"),
            "iar_demo_pillars": item.get("iar_demo_pillars"),
            "updated_at": "now()",
        })
    _upsert(client, "ingecart_events", rows, conflict_col="event_code", dry_run=dry_run)


# ---------------------------------------------------------------------------
# Seed: Documents
# ---------------------------------------------------------------------------

def seed_documents(client, dry_run: bool = False) -> None:
    print("\n[Documents]")

    document_specs: list[dict] = [
        # Executive report (informes/)
        {
            "path": _INFORMES_DIR / "informe_ejecutivo_IAR_FESPA_2026.txt",
            "title": "Informe Ejecutivo: Oportunidad Estratégica FESPA Barcelona 2026 — IAR × Ingecart",
            "category": "report",
            "subcategory": "executive_report",
            "source_type": "txt",
            "language": "es",
            "client_ref": "ingecart",
            "reference_code": "IE-IAR-FESPA-2026-001",
            "document_date": "2026-05-09",
            "tags": ["fespa", "iar", "ingecart", "strategic_analysis", "2026"],
        },
        # Research: company profile
        {
            "path": _RESEARCH_DIR / "company_profile" / "ingecart_company_profile.md",
            "title": "Ingecart — Company Profile",
            "category": "research",
            "subcategory": "company_profile",
            "source_type": "md",
            "language": "en",
            "client_ref": "ingecart",
            "tags": ["ingecart", "company_profile", "b2b"],
        },
        # Research: market intelligence
        {
            "path": _RESEARCH_DIR / "market_intelligence" / "ingecart_market_intelligence.md",
            "title": "Ingecart — Market Intelligence: Printing & Signage Sector 2024-2026",
            "category": "research",
            "subcategory": "market_intelligence",
            "source_type": "md",
            "language": "en",
            "client_ref": "ingecart",
            "tags": ["ingecart", "market_intelligence", "fespa", "printing", "signage"],
        },
        # Research: product catalog
        {
            "path": _RESEARCH_DIR / "products" / "ingecart_product_catalog.md",
            "title": "Ingecart — Product & Equipment Catalog",
            "category": "research",
            "subcategory": "product_catalog",
            "source_type": "md",
            "language": "en",
            "client_ref": "ingecart",
            "tags": ["ingecart", "products", "equipment", "catalog"],
        },
        # Marketing kit: pitch deck
        {
            "path": _MARKETING_KIT_DIR / "pitch_decks" / "ingecart_iar_fespa2026_pitch.md",
            "title": "IAR × Ingecart — FESPA Barcelona 2026: Pitch Talking Points",
            "category": "marketing_kit",
            "subcategory": "pitch_deck",
            "source_type": "md",
            "language": "es",
            "client_ref": "ingecart",
            "tags": ["ingecart", "pitch", "fespa", "2026", "marketing"],
        },
        # Marketing kit: ROI calculator
        {
            "path": _MARKETING_KIT_DIR / "roi_calculators" / "ingecart_ai_roi_calculator.md",
            "title": "IAR AI Agents — ROI Calculator for Ingecart Customers",
            "category": "roi_calculator",
            "subcategory": "ai_roi",
            "source_type": "md",
            "language": "en",
            "client_ref": "ingecart",
            "tags": ["ingecart", "roi", "calculator", "ai_agents"],
        },
    ]

    rows = []
    for spec in document_specs:
        path: Path = spec["path"]
        if not path.exists():
            print(f"  ⚠ File not found, skipping: {path.relative_to(_REPO_ROOT)}")
            continue
        raw_text = _read_text(path)
        row = {
            "title": spec["title"],
            "category": spec["category"],
            "subcategory": spec.get("subcategory"),
            "file_path": str(path.relative_to(_REPO_ROOT)),
            "filename": path.name,
            "source_type": spec.get("source_type", "txt"),
            "language": spec.get("language", "es"),
            "raw_text": raw_text,
            "tags": spec.get("tags", []),
            "client_ref": spec.get("client_ref", "ingecart"),
            "reference_code": spec.get("reference_code"),
            "document_date": spec.get("document_date"),
            "word_count": _word_count(raw_text),
            "checksum": _checksum(raw_text),
            "updated_at": "now()",
        }
        rows.append(row)

    _upsert(client, "ingecart_documents", rows, conflict_col="checksum", dry_run=dry_run)


# ---------------------------------------------------------------------------
# Seed: Research Entries
# ---------------------------------------------------------------------------

def seed_research_entries(client, dry_run: bool = False) -> None:
    print("\n[Research Entries]")
    mi_path = _RESEARCH_DIR / "market_intelligence" / "ingecart_market_intelligence.json"
    if not mi_path.exists():
        print("  ⚠ Market intelligence JSON not found, skipping.")
        return
    data: dict = _load_json(mi_path)

    rows = []

    # Trend entries
    for trend in data.get("dominant_trends", []):
        rows.append({
            "entry_type": "trend",
            "title": trend.get("trend"),
            "source": "IS-BACKOFFICE Market Analysis — IE-IAR-FESPA-2026-001",
            "source_date": "2026-05-09",
            "structured_data": trend,
            "tags": ["ingecart", "printing", "signage", "trend"],
            "relevance_score": 0.90,
            "verified": True,
        })

    # Competitive landscape entries
    for comp in data.get("competitive_landscape", []):
        rows.append({
            "entry_type": "competitive_intel",
            "title": f"Competitive Category: {comp.get('type')}",
            "source": "IS-BACKOFFICE Market Analysis",
            "source_date": "2026-05-09",
            "structured_data": comp,
            "tags": ["ingecart", "competitive_intel", comp.get("type", "")],
            "relevance_score": 0.80,
            "verified": True,
        })

    _upsert(client, "ingecart_research_entries", rows, dry_run=dry_run)


# ---------------------------------------------------------------------------
# Seed: Market Intelligence snapshot
# ---------------------------------------------------------------------------

def seed_market_intelligence(client, dry_run: bool = False) -> None:
    print("\n[Market Intelligence Snapshot]")
    mi_path = _RESEARCH_DIR / "market_intelligence" / "ingecart_market_intelligence.json"
    if not mi_path.exists():
        print("  ⚠ Market intelligence JSON not found, skipping.")
        return
    data: dict = _load_json(mi_path)

    row = {
        "snapshot_date": data.get("last_updated", str(date.today())),
        "sector": data.get("sector", "Printing, Signage & Visual Communication"),
        "period": data.get("period"),
        "key_metrics": data.get("key_metrics"),
        "trends": data.get("dominant_trends"),
        "competitive_landscape": data.get("competitive_landscape"),
        "target_segments": data.get("target_segments"),
        "financial_model": data.get("fespa_collaboration_financials"),
        "source_refs": [s.get("reference") for s in data.get("data_sources", [])
                        if s.get("reference")],
        "updated_at": "now()",
    }
    _upsert(client, "ingecart_market_intelligence", [row], dry_run=dry_run)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

SEED_FUNCTIONS = {
    "company": seed_company,
    "products": seed_products,
    "events": seed_events,
    "documents": seed_documents,
    "research_entries": seed_research_entries,
    "market_intelligence": seed_market_intelligence,
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed Ingecart data into Supabase."
    )
    parser.add_argument(
        "--source",
        choices=list(SEED_FUNCTIONS.keys()) + ["all"],
        default="all",
        help="Which data source to seed (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without writing to Supabase",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("IS-BACKOFFICE — Ingecart Supabase Seeder")
    print("=" * 60)

    if args.dry_run:
        print(">>> DRY RUN MODE — No data will be written <<<\n")

    supabase = get_supabase_client()
    if supabase is None:
        if args.dry_run:
            print("⚠ Supabase not configured — running in dry-run mode only.\n")
            # Use a dummy client for dry-run
            class _DummyClient:
                def table(self, name):
                    return self
                def upsert(self, *a, **kw):
                    return self
                def execute(self):
                    return None
            supabase_client = _DummyClient()
        else:
            print(
                "✗ Supabase is not configured.\n"
                "  Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables.\n"
                "  Tip: copy .env.example to .env and fill in your credentials."
            )
            sys.exit(1)
    else:
        supabase_client = supabase

    sources = (
        list(SEED_FUNCTIONS.keys())
        if args.source == "all"
        else [args.source]
    )

    for source in sources:
        SEED_FUNCTIONS[source](supabase_client, dry_run=args.dry_run)

    print("\n" + "=" * 60)
    print("Seeding complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
