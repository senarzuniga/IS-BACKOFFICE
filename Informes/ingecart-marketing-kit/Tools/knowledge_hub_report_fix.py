#!/usr/bin/env python3
"""
Knowledge Hub Reporting Fix (Mode V1)
- Scans a given directory (file-first)
- Produces Evidence Base (file list + metadata)
- Generates a Data Contract of required inputs
- Validates presence of required inputs in local files only
- Produces structured extracted data and validation report
- Enforces >90% grounding before allowing executive report generation

Usage:
  python knowledge_hub_report_fix.py --dir "C:\\path\\to\\folder" --outdir ../Output

This script is strictly local-file based and performs no network activity.
"""

import os
import sys
import json
import re
import argparse
import mimetypes
from datetime import datetime, timezone


DEFAULT_REQUIRED = {
    "financial_inputs": [
        "audited_p_and_l",
        "balance_sheet",
        "cash_position",
        "ebitda",
        "revenue",
        "gross_margin",
        "accounts_receivable",
        "accounts_payable",
        "debt",
        "capex"
    ],
    "project_inputs": [
        "project_scope",
        "project_capex",
        "project_costs",
        "project_timeline",
        "vendor_support",
        "site_survey",
        "utility_requirements"
    ],
    "risk_inputs": [
        "operational_risks",
        "safety_risks",
        "supply_chain_risks",
        "financial_risks",
        "regulatory_risks"
    ],
    "client_inputs": [
        "customer_list",
        "backlog",
        "contract_terms",
        "customer_concentration"
    ]
}


# Mapping of contract key -> search phrases (case-insensitive)
KEY_PHRASES = {
    # Financial
    "audited_p_and_l": ["audited financial statements", "audited p&l", "audited profit and loss", "auditor"],
    "balance_sheet": ["balance sheet", "statement of financial position"],
    "cash_position": ["cash position", "cash balance", "cash at bank", "cash and cash equivalents"],
    "ebitda": ["ebitda", "e\.b\.i\.t\.d\.a"],
    "revenue": ["revenue", "turnover", "sales", "ingresos", "ventas"],
    "gross_margin": ["gross margin", "margen bruto", "margen"],
    "accounts_receivable": ["accounts receivable", "trade receivables", "cuentas por cobrar"],
    "accounts_payable": ["accounts payable", "trade payables", "cuentas por pagar"],
    "debt": ["debt", "long[- ]term debt", "loan", "deuda"],
    "capex": ["capex", "capital expenditure", "capex"],
    # Project
    "project_scope": ["scope of work", "project scope", "alcance del proyecto"],
    "project_capex": ["project capex", "capex"],
    "project_costs": ["costs", "cost base", "costs breakdown"],
    "project_timeline": ["timeline", "schedule", "plazo", "duración"],
    "vendor_support": ["vendor support", "oem support", "written support", "BHS support"],
    "site_survey": ["site survey", "site survey report", "survey"],
    "utility_requirements": ["electrical", "steam", "utilities", "utility"],
    # Risk
    "operational_risks": ["operational risk", "operational risks", "riesgo operativo"],
    "safety_risks": ["safety", "seguridad", "accident"],
    "supply_chain_risks": ["supply chain", "supply", "logistics risk", "proveedor"],
    "financial_risks": ["financial risk", "financial risks", "riesgo financiero"],
    "regulatory_risks": ["regulator", "regulation", "regulatory"],
    # Client
    "customer_list": ["customer", "client list", "clientes", "clientes:", "customer list"],
    "backlog": ["backlog", "order backlog", "pedido pendiente"],
    "contract_terms": ["contract", "terms", "condiciones"],
    "customer_concentration": ["concentration", "top customer", "customer concentration"]
}

CURRENCY_PATTERNS = [
    r"€\s?[\d\.,]+",
    r"EUR\s?[\d\.,]+",
    r"\$\s?[\d\.,]+",
    r"USD\s?[\d\.,]+",
    r"\b[\d]{1,3}(?:[\.,][\d]{3})+(?:[\.,][\d]{2})?\b"  # numbers with thousands separators
]


def scan_directory(path):
    entries = []
    now = datetime.now(timezone.utc).isoformat()
    try:
        for entry in os.scandir(path):
            if entry.is_file():
                st = entry.stat()
                entries.append({
                    "name": entry.name,
                    "full_path": os.path.abspath(entry.path),
                    "size_bytes": st.st_size,
                    "last_modified": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat()
                })
        return {"scan_time": now, "files": entries}
    except Exception as e:
        raise


def read_text_file(path):
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except Exception:
            continue
    return ""


def search_in_text(text, phrases):
    results = []
    lower = text.lower()
    for phrase in phrases:
        if phrase.lower() in lower:
            # find first occurrence position
            idx = lower.find(phrase.lower())
            start = max(0, idx - 120)
            end = min(len(text), idx + len(phrase) + 120)
            excerpt = text[start:end].strip()
            # compute line number
            line_no = text[:idx].count("\n") + 1
            results.append({"phrase": phrase, "excerpt": excerpt, "line": line_no})
    return results


def find_currency_matches(text):
    matches = []
    for pat in CURRENCY_PATTERNS:
        for m in re.finditer(pat, text):
            start = max(0, m.start() - 60)
            end = min(len(text), m.end() + 60)
            matches.append({"match": m.group(0), "excerpt": text[start:end].strip(), "line": text[:m.start()].count("\n") + 1})
    return matches


def build_data_contract(required=DEFAULT_REQUIRED):
    contract = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "required_inputs": required
    }
    return contract


def validate_and_extract(dir_path, scan, contract):
    # prepare results for each required key
    all_required = []
    for cat, keys in contract["required_inputs"].items():
        all_required.extend(keys)
    extracted = {k: [] for k in all_required}

    files_used = []

    for f in scan["files"]:
        path = f["full_path"]
        text = read_text_file(path)
        if not text:
            continue
        files_used.append(path)
        for key in all_required:
            phrases = KEY_PHRASES.get(key, [])
            matches = search_in_text(text, phrases) if phrases else []
            currency_matches = []
            # for financial-related keys also try to find currency numbers
            if key in contract['required_inputs'].get('financial_inputs', []):
                currency_matches = find_currency_matches(text)
            if matches or currency_matches:
                extracted[key].append({
                    "file": path,
                    "phrases_found": matches,
                    "currency_found": currency_matches
                })
    return extracted, files_used


def produce_reports(outdir, evidence, contract, extracted, files_used):
    os.makedirs(outdir, exist_ok=True)
    evidence_path = os.path.join(outdir, "evidence_base.json")
    contract_path = os.path.join(outdir, "data_contract.json")
    extracted_path = os.path.join(outdir, "data_extracted.json")

    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, ensure_ascii=False)

    with open(contract_path, "w", encoding="utf-8") as f:
        json.dump(contract, f, indent=2, ensure_ascii=False)

    report = {
        "report_generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_base": evidence,
        "data_contract": contract,
        "extracted_data": extracted,
        "files_used": files_used
    }
    with open(extracted_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return evidence_path, contract_path, extracted_path


def compute_validation(contract, extracted):
    all_required = []
    for cat, keys in contract["required_inputs"].items():
        all_required.extend(keys)
    total = len(all_required)
    found = sum(1 for k in all_required if extracted.get(k))
    percent_grounded = 100.0 * found / total if total else 100.0
    missing = [k for k in all_required if not extracted.get(k)]

    # number of unverified claims = any missing
    unverified_claims = len(missing)

    validation = {
        "total_required_inputs": total,
        "found_required_inputs": found,
        "percent_grounded": percent_grounded,
        "missing_inputs": missing,
        "unverified_claims": unverified_claims
    }
    return validation


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=True, help="Directory to scan (file-first evidence source)")
    parser.add_argument("--outdir", default=os.path.join(os.path.dirname(__file__), "..", "Output"), help="Output folder for reports")
    parser.add_argument("--write-strings", action="store_true", help="Write concise human-readable report (debug)")
    args = parser.parse_args()

    target = args.dir
    outdir = os.path.abspath(args.outdir)

    # Step 1: Scan directory
    try:
        evidence = scan_directory(target)
    except Exception as e:
        print("ERROR: Failed scanning directory:", e)
        sys.exit(1)

    if not evidence["files"]:
        print("ERROR: No files found in directory. Stopping execution.")
        sys.exit(1)

    # Step 2: Build data contract and save
    contract = build_data_contract()

    # Step 3: Validate and extract
    extracted, files_used = validate_and_extract(target, evidence, contract)

    # Step 4: Produce reports
    evidence_path, contract_path, extracted_path = produce_reports(outdir, evidence, contract, extracted, files_used)

    # Step 5: Compute validation
    validation = compute_validation(contract, extracted)
    validation_path = os.path.join(outdir, "validation_summary.json")
    with open(validation_path, "w", encoding="utf-8") as f:
        json.dump(validation, f, indent=2, ensure_ascii=False)

    # Output summary to stdout
    print("Evidence base saved to:", evidence_path)
    print("Data contract saved to:", contract_path)
    print("Extracted data report saved to:", extracted_path)
    print("Validation summary saved to:", validation_path)
    print(json.dumps(validation, indent=2, ensure_ascii=False))

    # Enforce validation gate
    if validation["percent_grounded"] < 90.0 or validation["unverified_claims"] > 0:
        print("INCOMPLETE DATA SET")
        # Exit non-zero to indicate failure to generate executive report
        sys.exit(2)

    # If passes, optionally write a minimal human-readable summary
    if args.write_strings:
        hr = os.path.join(outdir, "executive_summary.txt")
        with open(hr, "w", encoding="utf-8") as f:
            f.write("EXECUTIVE REPORT — Data grounded >90%\n\n")
            f.write("Evidence base files:\n")
            for fi in evidence["files"]:
                f.write(f"- {fi['full_path']} ({fi['size_bytes']} bytes)\n")
            f.write("\nValidation:\n")
            f.write(json.dumps(validation, indent=2, ensure_ascii=False))
        print("Human-readable summary written to", hr)

    print("Validation passed — data grounding OK. Executive report generation may proceed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
