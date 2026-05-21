from __future__ import annotations

import json
import os
import re
import sqlite3
from pathlib import Path

import requests
from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = REPO_ROOT / "research" / "ingecart" / "web_scraping" / "FESPA_2026_Barcelona_Exhibitors_Complete.json"
SOURCE_LABEL = "FESPA 2026 Exhibitor Intelligence Dataset"
TABLE_NAME = "ingecart_research_entries"
LOCAL_DB_PATH = REPO_ROOT / "research" / "ingecart" / "company_intelligence.db"
TRADING_CSV_PATH = REPO_ROOT / "research" / "ingecart" / "machine_trading_company_view.csv"
TRADING_MD_PATH = REPO_ROOT / "research" / "ingecart" / "machine_trading_company_view.md"


def clamp_score(score: int) -> int:
    return max(0, min(100, score))


def normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def interest_level(score: int) -> str:
    if score >= 80:
        return "high"
    if score >= 60:
        return "medium"
    return "low"


def infer_ingecart_fit(name: str, group_key: str, category: str, products: list[str]) -> tuple[str, int]:
    direct_competitors = {
        "fosber",
        "bobst",
        "comexi",
        "heidelberg",
        "krones",
        "azionaria",
    }
    supplier_terms = {"inks", "coatings", "supplies", "plates"}
    software_terms = {"software", "workflow", "mis/erp", "management"}
    automation_terms = {"automation", "robotics"}

    normalized_name = normalize_token(name)
    category_l = category.lower()
    products_l = " ".join(products).lower()

    if normalized_name in direct_competitors:
        return "direct_competitor", 90

    if any(term in products_l for term in supplier_terms):
        return "supplier", 62

    if group_key == "software_services" or any(term in category_l or term in products_l for term in software_terms):
        return "technology_partner", 74

    if group_key == "automation" or any(term in category_l or term in products_l for term in automation_terms):
        return "automation_partner", 72

    if group_key == "corrugated_packaging":
        return "competitor_or_benchmark", 82

    if group_key == "print_graphics":
        return "adjacent_player", 63

    return "market_player", 58


def infer_other_business_fit(group_key: str, category: str, products: list[str]) -> tuple[list[str], int]:
    category_l = category.lower()
    products_l = " ".join(products).lower()

    profiles = [
        "industrial_distributor",
        "system_integrator",
        "international_sales_partner",
    ]
    score = 65

    if group_key == "software_services" or "software" in category_l or "workflow" in products_l:
        profiles.extend(["software_reseller", "digital_transformation_consultancy"])
        score += 18

    if group_key == "automation" or "automation" in category_l or "robotics" in products_l:
        profiles.extend(["automation_integrator", "robotics_solution_provider"])
        score += 15

    if "corrugated" in category_l or "packaging" in category_l:
        profiles.extend(["packaging_converter", "box_manufacturer"])
        score += 12

    if "printing" in category_l or "print" in category_l:
        profiles.extend(["commercial_printer", "print_service_provider"])
        score += 10

    return sorted(set(profiles)), clamp_score(score)


def infer_machine_trading_fit(group_key: str, category: str, products: list[str]) -> tuple[str, list[str], int]:
    category_l = category.lower()
    products_l = " ".join(products).lower()

    use_cases = [
        "buyer_discovery",
        "competitor_tracking",
    ]
    score = 64
    fit_type = "market_signal_target"

    if "corrugated" in category_l or "packaging" in category_l:
        use_cases.extend(["ffg_market_mapping", "corrugated_capacity_tracking"])
        score += 18
        fit_type = "core_trading_target"

    if "automation" in category_l or "robotics" in products_l:
        use_cases.extend(["automation_upgrade_leads", "plant_modernization_signals"])
        score += 14

    if "software" in category_l or "workflow" in products_l:
        use_cases.extend(["martech_partner_mapping", "workflow_stack_intelligence"])
        score += 10

    if "printing" in category_l or "print" in category_l:
        use_cases.extend(["print_converter_lead_graph", "equipment_renewal_signals"])
        score += 10

    score = clamp_score(score)
    if score >= 85:
        fit_type = "priority_trading_target"

    return fit_type, sorted(set(use_cases)), score


def build_analysis(exhibitor: dict, group_key: str, compiled_date: str | None) -> dict:
    name = exhibitor.get("name", "Unknown")
    category = exhibitor.get("category", "Unknown")
    products = exhibitor.get("products", []) or []
    country = exhibitor.get("country", "Unknown")

    ingecart_fit, ingecart_score = infer_ingecart_fit(name, group_key, category, products)
    other_profiles, other_score = infer_other_business_fit(group_key, category, products)
    trading_fit, trading_use_cases, trading_score = infer_machine_trading_fit(group_key, category, products)

    if country.lower() == "spain":
        ingecart_score = clamp_score(ingecart_score + 6)

    summary = (
        f"{name} operates in '{category}' with focus on {', '.join(products) or 'n/a'}. "
        f"Ingecart fit: {ingecart_fit} ({ingecart_score}/100). "
        f"Machine-Trading fit: {trading_fit} ({trading_score}/100). "
        f"Cross-business fit: {interest_level(other_score)} ({other_score}/100)."
    )

    return {
        "company_name": name,
        "activity": category,
        "location": {
            "country": country,
            "city": None,
        },
        "website": exhibitor.get("website"),
        "products": products,
        "fespa": {
            "event": "FESPA Global Print Expo 2026",
            "category_group": group_key,
            "booth_focus": exhibitor.get("booth_focus"),
            "history": exhibitor.get("fespa_history"),
            "rank_in_group": exhibitor.get("rank"),
        },
        "qualification": {
            "ingecart_fit_type": ingecart_fit,
            "ingecart_interest_score": ingecart_score,
            "ingecart_interest_level": interest_level(ingecart_score),
            "machine_trading_fit_type": trading_fit,
            "machine_trading_interest_score": trading_score,
            "machine_trading_interest_level": interest_level(trading_score),
            "machine_trading_use_cases": trading_use_cases,
            "other_business_interest_score": other_score,
            "other_business_interest_level": interest_level(other_score),
            "recommended_business_profiles": other_profiles,
        },
        "analysis_summary": summary,
        "data_quality": "high",
        "last_reviewed_at": compiled_date,
    }


def build_rows(data: dict) -> list[dict]:
    rows: list[dict] = []
    compiled_date = data.get("research_metadata", {}).get("date_compiled")
    category_map = data.get("exhibitors_by_category", {})

    for group_key, exhibitors in category_map.items():
        for exhibitor in exhibitors:
            analysis = build_analysis(exhibitor, group_key, compiled_date)
            company_name = analysis["company_name"]
            tags = [
                "ingecart",
                "fespa_2026",
                "exhibitor_intelligence",
                normalize_token(group_key),
                normalize_token(analysis["location"]["country"]),
                normalize_token(company_name),
            ]

            rows.append(
                {
                    "entry_type": "competitive_intel",
                    "title": f"FESPA 2026 Exhibitor - {company_name}",
                    "source": SOURCE_LABEL,
                    "source_date": "2026-05-13",
                    "content": analysis["analysis_summary"],
                    "structured_data": analysis,
                    "tags": tags,
                    "relevance_score": round(analysis["qualification"]["ingecart_interest_score"] / 100, 2),
                    "verified": True,
                }
            )

    return rows


def persist_local_sqlite(rows: list[dict]) -> int:
    LOCAL_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(LOCAL_DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS company_intelligence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_dataset TEXT NOT NULL,
                company_name TEXT NOT NULL,
                activity TEXT,
                country TEXT,
                city TEXT,
                website TEXT,
                products_json TEXT,
                category_group TEXT,
                booth_focus TEXT,
                fespa_history TEXT,
                rank_in_group INTEGER,
                ingecart_fit_type TEXT,
                ingecart_interest_score INTEGER,
                ingecart_interest_level TEXT,
                machine_trading_fit_type TEXT,
                machine_trading_interest_score INTEGER,
                machine_trading_interest_level TEXT,
                machine_trading_use_cases_json TEXT,
                other_business_interest_score INTEGER,
                other_business_interest_level TEXT,
                recommended_profiles_json TEXT,
                analysis_summary TEXT,
                relevance_score REAL,
                verified INTEGER,
                source_date TEXT,
                raw_payload_json TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source_dataset, company_name)
            )
            """
        )

        cur.execute("PRAGMA table_info(company_intelligence)")
        existing_cols = {row[1] for row in cur.fetchall()}
        required_new_cols = {
            "machine_trading_fit_type": "TEXT",
            "machine_trading_interest_score": "INTEGER",
            "machine_trading_interest_level": "TEXT",
            "machine_trading_use_cases_json": "TEXT",
        }
        for col_name, col_type in required_new_cols.items():
            if col_name not in existing_cols:
                cur.execute(f"ALTER TABLE company_intelligence ADD COLUMN {col_name} {col_type}")

        for row in rows:
            payload = row["structured_data"]
            q = payload["qualification"]
            f = payload["fespa"]
            l = payload["location"]
            cur.execute(
                """
                INSERT INTO company_intelligence (
                    source_dataset,
                    company_name,
                    activity,
                    country,
                    city,
                    website,
                    products_json,
                    category_group,
                    booth_focus,
                    fespa_history,
                    rank_in_group,
                    ingecart_fit_type,
                    ingecart_interest_score,
                    ingecart_interest_level,
                    machine_trading_fit_type,
                    machine_trading_interest_score,
                    machine_trading_interest_level,
                    machine_trading_use_cases_json,
                    other_business_interest_score,
                    other_business_interest_level,
                    recommended_profiles_json,
                    analysis_summary,
                    relevance_score,
                    verified,
                    source_date,
                    raw_payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_dataset, company_name) DO UPDATE SET
                    activity=excluded.activity,
                    country=excluded.country,
                    city=excluded.city,
                    website=excluded.website,
                    products_json=excluded.products_json,
                    category_group=excluded.category_group,
                    booth_focus=excluded.booth_focus,
                    fespa_history=excluded.fespa_history,
                    rank_in_group=excluded.rank_in_group,
                    ingecart_fit_type=excluded.ingecart_fit_type,
                    ingecart_interest_score=excluded.ingecart_interest_score,
                    ingecart_interest_level=excluded.ingecart_interest_level,
                    machine_trading_fit_type=excluded.machine_trading_fit_type,
                    machine_trading_interest_score=excluded.machine_trading_interest_score,
                    machine_trading_interest_level=excluded.machine_trading_interest_level,
                    machine_trading_use_cases_json=excluded.machine_trading_use_cases_json,
                    other_business_interest_score=excluded.other_business_interest_score,
                    other_business_interest_level=excluded.other_business_interest_level,
                    recommended_profiles_json=excluded.recommended_profiles_json,
                    analysis_summary=excluded.analysis_summary,
                    relevance_score=excluded.relevance_score,
                    verified=excluded.verified,
                    source_date=excluded.source_date,
                    raw_payload_json=excluded.raw_payload_json,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    SOURCE_LABEL,
                    payload["company_name"],
                    payload["activity"],
                    l.get("country"),
                    l.get("city"),
                    payload.get("website"),
                    json.dumps(payload.get("products", []), ensure_ascii=False),
                    f.get("category_group"),
                    f.get("booth_focus"),
                    f.get("history"),
                    f.get("rank_in_group"),
                    q.get("ingecart_fit_type"),
                    q.get("ingecart_interest_score"),
                    q.get("ingecart_interest_level"),
                    q.get("machine_trading_fit_type"),
                    q.get("machine_trading_interest_score"),
                    q.get("machine_trading_interest_level"),
                    json.dumps(q.get("machine_trading_use_cases", []), ensure_ascii=False),
                    q.get("other_business_interest_score"),
                    q.get("other_business_interest_level"),
                    json.dumps(q.get("recommended_business_profiles", []), ensure_ascii=False),
                    payload.get("analysis_summary"),
                    row.get("relevance_score"),
                    1 if row.get("verified") else 0,
                    row.get("source_date"),
                    json.dumps(row, ensure_ascii=False),
                ),
            )

        conn.commit()
        cur.execute(
            "SELECT COUNT(*) FROM company_intelligence WHERE source_dataset = ?",
            (SOURCE_LABEL,),
        )
        total = int(cur.fetchone()[0])
        export_trading_views(conn)
        return total
    finally:
        conn.close()


def export_trading_views(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            company_name,
            activity,
            country,
            website,
            machine_trading_fit_type,
            machine_trading_interest_score,
            machine_trading_interest_level,
            machine_trading_use_cases_json,
            ingecart_interest_score,
            other_business_interest_score,
            analysis_summary
        FROM company_intelligence
        WHERE source_dataset = ?
        ORDER BY machine_trading_interest_score DESC, ingecart_interest_score DESC, company_name ASC
        """,
        (SOURCE_LABEL,),
    )
    rows = cur.fetchall()

    TRADING_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(TRADING_CSV_PATH, "w", encoding="utf-8") as f:
        f.write(
            "company_name,activity,country,website,machine_trading_fit_type,machine_trading_interest_score,"
            "machine_trading_interest_level,machine_trading_use_cases,ingecart_interest_score,"
            "other_business_interest_score,analysis_summary\n"
        )
        for row in rows:
            cleaned = []
            for item in row:
                text = "" if item is None else str(item)
                text = text.replace('"', '""')
                cleaned.append(f'"{text}"')
            f.write(",".join(cleaned) + "\n")

    top = rows[:12]
    with open(TRADING_MD_PATH, "w", encoding="utf-8") as f:
        f.write("# Machine-Trading Business View\n\n")
        f.write("This report lists companies ranked by machine-trading interest score.\n\n")
        f.write("| Company | Activity | Country | Trading Fit | Trading Score | Ingecart Score | Other Business Score |\n")
        f.write("|---|---|---|---|---:|---:|---:|\n")
        for row in top:
            f.write(
                f"| {row[0]} | {row[1]} | {row[2]} | {row[4]} | {row[5]} | {row[8]} | {row[9]} |\n"
            )

        f.write("\n## Notes\n")
        f.write("- Full dataset is available in machine_trading_company_view.csv.\n")
        f.write("- Source dataset: FESPA 2026 Exhibitor Intelligence Dataset.\n")


def main() -> None:
    load_dotenv()

    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not service_key:
        raise SystemExit("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in environment.")

    if not DATA_PATH.exists():
        raise SystemExit(f"Data file not found: {DATA_PATH}")

    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    rows = build_rows(data)

    base = supabase_url.rstrip("/") + "/rest/v1"
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
    }

    delete_params = {
        "source": f"eq.{SOURCE_LABEL}",
    }
    delete_resp = requests.delete(f"{base}/{TABLE_NAME}", headers=headers, params=delete_params, timeout=30)

    if delete_resp.status_code == 404:
        total = persist_local_sqlite(rows)
        print("Supabase table not found; stored data in local SQLite fallback.")
        print(f"SQLite DB: {LOCAL_DB_PATH}")
        print(f"Stored rows: {total}")
        return

    if delete_resp.status_code >= 400:
        raise SystemExit(f"Delete failed ({delete_resp.status_code}): {delete_resp.text}")

    insert_headers = headers | {"Prefer": "return=representation"}
    insert_resp = requests.post(f"{base}/{TABLE_NAME}", headers=insert_headers, json=rows, timeout=60)
    if insert_resp.status_code >= 400:
        raise SystemExit(f"Insert failed ({insert_resp.status_code}): {insert_resp.text}")

    inserted = insert_resp.json()
    print(f"Inserted rows: {len(inserted)}")

    count_headers = headers | {"Prefer": "count=exact", "Range": "0-0"}
    count_params = {"source": f"eq.{SOURCE_LABEL}", "select": "id"}
    count_resp = requests.get(f"{base}/{TABLE_NAME}", headers=count_headers, params=count_params, timeout=30)
    if count_resp.status_code >= 400:
        raise SystemExit(f"Count check failed ({count_resp.status_code}): {count_resp.text}")

    content_range = count_resp.headers.get("Content-Range", "")
    print(f"Stored rows with source '{SOURCE_LABEL}': {content_range}")


if __name__ == "__main__":
    main()
