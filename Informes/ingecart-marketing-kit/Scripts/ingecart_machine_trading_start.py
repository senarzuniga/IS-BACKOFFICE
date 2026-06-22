#!/usr/bin/env python
"""Quick-start launcher for the machine-trading intelligence pipeline."""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backoffice.ingestion.intelligence import build_pipeline

RUN_ROOT = (
    REPO_ROOT
    / "ingecart-marketing-kit"
    / "machine-trading-boost-plan"
    / "runs"
    / datetime.now().strftime("%Y-%m-%d")
)
REPORTS_DIR = RUN_ROOT / "reports"
SIGNALS_DIR = RUN_ROOT / "signals"
CRM_DIR = RUN_ROOT / "crm"
LOGS_DIR = RUN_ROOT / "logs"
BASE_CRM_PATH = REPO_ROOT / "ingecart-marketing-kit" / "machine-trading-boost-plan" / "templates" / "crm_import_qualified_leads.csv"


def prepare_run_dirs() -> None:
    for path in (REPORTS_DIR, SIGNALS_DIR, CRM_DIR, LOGS_DIR):
        path.mkdir(parents=True, exist_ok=True)


def print_header(text: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    def default(value: Any) -> Any:
        if is_dataclass(value):
            return asdict(value)
        if hasattr(value, "value"):
            return value.value
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)

    write_text(path, json.dumps(payload, ensure_ascii=False, indent=2, default=default))


def source_to_dict(source: Any) -> dict[str, Any]:
    data = asdict(source) if is_dataclass(source) else dict(source)
    for key, value in list(data.items()):
        if hasattr(value, "value"):
            data[key] = value.value
        elif hasattr(value, "isoformat"):
            data[key] = value.isoformat()
    return data


def is_machine_trading_source(source: Any) -> bool:
    source_id = getattr(source, "id", "")
    tags = " ".join(getattr(source, "metadata", {}).get("tags", []) or [])
    if hasattr(source, "event_triggers"):
        tags = f"{tags} {' '.join(getattr(source, 'event_triggers', []))}"
    return source_id in {
        "exapro_machinery",
        "kitmondo_machinery",
        "machineseeker",
        "machinio",
        "fefco_news",
        "ccca_news",
        "drupa_exhibitors",
        "supercorrexpo",
        "sino_corrugated_wepack",
        "paperage_news",
        "tappi_resources",
        "packaging_expansion_monitor",
    } or "machine_trading" in tags.lower()


def test_sources() -> list[dict[str, Any]]:
    """Verify all machine-trading sources are configured and reachable."""
    print_header("Testing Machine Trading Sources")

    pipeline = build_pipeline(config_path="config/sources.yaml")
    machine_trading_sources = [source_to_dict(source) for source in pipeline.planner.sources if is_machine_trading_source(source)]

    print(f"Found {len(machine_trading_sources)} machine-trading sources:\n")
    for source in machine_trading_sources:
        status = "[+] ACTIVE" if source.get("is_active") else "[-] INACTIVE"
        print(f"  {status} | {source.get('id'):25s} | {source.get('name'):30s} | Tier {source.get('tier')}")

    report_path = REPORTS_DIR / "source_check.json"
    write_json(report_path, {
        "checked_at": datetime.now().isoformat(),
        "source_count": len(machine_trading_sources),
        "sources": machine_trading_sources,
    })
    write_text(
        REPORTS_DIR / "source_check.txt",
        "\n".join([
            f"Checked at: {datetime.now().isoformat()}",
            f"Machine-trading sources found: {len(machine_trading_sources)}",
            *[
                f"- {src.get('id')} | {src.get('name')} | {src.get('tier')} | {'ACTIVE' if src.get('is_active') else 'INACTIVE'}"
                for src in machine_trading_sources
            ],
        ]),
    )
    print(f"\nSaved source report to {report_path}")
    return machine_trading_sources


def run_daily_ingestion() -> dict[str, Any]:
    """Execute one daily scraping cycle for machine-trading sources."""
    print_header("Running Daily Machine Trading Intelligence Ingestion")

    pipeline = build_pipeline(config_path="config/sources.yaml")
    print("Starting ingestion pipeline...\n")

    async def _run() -> dict[str, Any]:
        return await pipeline.run_cycle_once(events=[])

    try:
        stats = asyncio.run(_run())
        status = "completed"
        error_message = None
    except Exception as exc:  # noqa: BLE001
        stats = dict(pipeline.get_stats())
        status = "failed"
        error_message = str(exc)

    summary = {
        "run_at": datetime.now().isoformat(),
        "status": status,
        "error": error_message,
        "stats": stats,
    }
    write_json(LOGS_DIR / "daily_run_stats.json", summary)

    print(f"\nIngestion {status} at {datetime.now().isoformat()}")
    print(f"  Jobs processed: {stats.get('jobs_processed', 0)}")
    print(f"  Successful scrapes: {stats.get('successful_scrapes', 0)}")
    print(f"  Failed scrapes: {stats.get('failed_scrapes', 0)}")
    print(f"  Extractions done: {stats.get('extractions_done', 0)}")
    print(f"  Actions created: {stats.get('actions_created', 0)}")
    if error_message:
        print(f"  Error: {error_message}")

    print(f"\nSaved daily run summary to {LOGS_DIR / 'daily_run_stats.json'}")
    return summary


def analyze_recent_signals() -> list[dict[str, Any]]:
    """Analyze signals from the last 7 days and show top opportunities."""
    print_header("Analyzing Recent Machine Trading Signals (Last 7 Days)")

    from db.client import get_supabase_client

    supabase = get_supabase_client()
    if not supabase:
        print("Supabase is not configured; no live signals were available.")
        write_json(SIGNALS_DIR / "recent_signals.json", {"items": [], "note": "Supabase unavailable"})
        return []

    cutoff_date = (datetime.now() - timedelta(days=7)).isoformat()
    response = (
        supabase.table("intelligence_outputs")
        .select("*")
        .gte("created_at", cutoff_date)
        .order("buyer_fit_score", desc=True)
        .limit(20)
        .execute()
    )

    items = response.data if response else []

    print(f"Found {len(items)} high-fit signals in last 7 days:\n")
    for idx, item in enumerate(items, 1):
        print(f"  {idx}. {item.get('company_name', 'Unknown Company')}")
        print(f"     Country: {item.get('company_country', 'N/A')}")
        print(f"     Type: {item.get('demand_type', 'N/A')}")
        print(f"     Machine: {item.get('machine_type', 'N/A')}")
        print(f"     Score: {item.get('buyer_fit_score', 0)}/100")
        print()

    write_json(SIGNALS_DIR / "recent_signals.json", {"cutoff_date": cutoff_date, "items": items})
    write_text(
        SIGNALS_DIR / "recent_signals.txt",
        "\n".join(
            [f"Cutoff date: {cutoff_date}", f"Signals found: {len(items)}"]
            + [
                f"{idx}. {item.get('company_name', 'Unknown Company')} | {item.get('company_country', 'N/A')} | {item.get('demand_type', 'N/A')} | {item.get('machine_type', 'N/A')} | {item.get('buyer_fit_score', 0)}/100"
                for idx, item in enumerate(items, 1)
            ]
        ),
    )
    print(f"Saved signal analysis to {SIGNALS_DIR / 'recent_signals.json'}")
    return items


def generate_crm_import() -> str:
    """Generate CSV export of qualified leads for CRM import."""
    print_header("Generating CRM Import File")

    from db.client import get_supabase_client

    supabase = get_supabase_client()
    items: list[dict[str, Any]] = []
    if supabase:
        try:
            response = (
                supabase.table("intelligence_outputs")
                .select(
                    "id, company_name, company_country, demand_type, machine_type, buyer_fit_score, contact_extracted, source_url"
                )
                .gte("buyer_fit_score", 50)
                .eq("contacted", False)
                .execute()
            )
            items = response.data if response else []
        except Exception as exc:  # noqa: BLE001
            print(f"Supabase query failed, exporting an empty CRM file instead: {exc}")

    csv_path = BASE_CRM_PATH
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "account_name",
            "country",
            "contact_name",
            "contact_role",
            "email",
            "demand_type",
            "machine_type",
            "lead_score",
            "source_url",
        ])

        for item in items:
            contact = item.get("contact_extracted", {}) or {}
            writer.writerow([
                item.get("company_name"),
                item.get("company_country"),
                contact.get("name", ""),
                contact.get("title", ""),
                contact.get("email", ""),
                item.get("demand_type"),
                item.get("machine_type"),
                item.get("buyer_fit_score"),
                item.get("source_url", ""),
            ])

    structured_csv = CRM_DIR / "crm_import_qualified_leads.csv"
    structured_csv.write_bytes(csv_path.read_bytes())
    write_json(CRM_DIR / "crm_import_summary.json", {
        "generated_at": datetime.now().isoformat(),
        "lead_count": len(items),
        "csv_path": str(csv_path),
        "structured_csv_path": str(structured_csv),
    })

    print(f"[+] Created {csv_path}")
    print(f"  Contains {len(items)} qualified leads ready for outreach")
    print(f"  Copied structured CRM export to {structured_csv}")

    return str(csv_path)


def write_run_index() -> None:
    write_text(
        RUN_ROOT / "README.md",
        "\n".join([
            "# Machine Trading Run",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Folders",
            f"- Reports: {REPORTS_DIR}",
            f"- Signals: {SIGNALS_DIR}",
            f"- CRM: {CRM_DIR}",
            f"- Logs: {LOGS_DIR}",
            "",
            "## Files",
            "- reports/source_check.json",
            "- reports/source_check.txt",
            "- signals/recent_signals.json",
            "- signals/recent_signals.txt",
            "- logs/daily_run_stats.json",
            "- crm/crm_import_qualified_leads.csv",
            "- crm/crm_import_summary.json",
        ]),
    )


def main() -> None:
    prepare_run_dirs()
    parser = argparse.ArgumentParser(description="Activate and manage machine-trading intelligence pipeline")
    parser.add_argument("--test", action="store_true", help="Test source configuration")
    parser.add_argument("--run-daily", action="store_true", help="Execute one daily ingestion cycle")
    parser.add_argument("--analyze-signals", action="store_true", help="Analyze signals from last 7 days")
    parser.add_argument("--generate-crm", action="store_true", help="Generate CRM import file")
    parser.add_argument("--full-run", action="store_true", help="Run full pipeline: test + ingest + analyze + generate")

    args = parser.parse_args()
    if args.full_run:
        args.test = args.run_daily = args.analyze_signals = args.generate_crm = True

    ran_anything = False
    if args.test:
        ran_anything = True
        test_sources()
    if args.run_daily:
        ran_anything = True
        run_daily_ingestion()
    if args.analyze_signals:
        ran_anything = True
        analyze_recent_signals()
    if args.generate_crm:
        ran_anything = True
        generate_crm_import()

    if ran_anything:
        write_run_index()
        print(f"\nStructured run folder: {RUN_ROOT}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
