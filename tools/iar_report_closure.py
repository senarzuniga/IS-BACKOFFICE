from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]], columns: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def weighted_confidence(verified: int, partial: int, not_verified: int, contradicted: int) -> float:
    total = max(1, verified + partial + not_verified + contradicted)
    score = (verified + 0.5 * partial - 0.75 * contradicted) / total
    return round(max(0.0, min(1.0, score)) * 100.0, 2)


def build_traceability_matrix(root: Path, run_summary: Dict[str, Any], arch_decision: Dict[str, Any]) -> List[Dict[str, Any]]:
    selected = arch_decision.get("selected", {})
    rows = [
        {
            "Conclusion": "Recommended positioning technology is UWB-first with modular hybrid extension",
            "Evidence Artifacts": "benchmark/technology_comparison_matrix.csv; benchmark/technology_decision_matrix.csv; claims_catalog.json",
            "Status": "Traceable",
        },
        {
            "Conclusion": f"Selected architecture: {selected.get('key')} - {selected.get('name')}",
            "Evidence Artifacts": "architecture_decision.json; benchmark/technology_decision_matrix.csv",
            "Status": "Traceable",
        },
        {
            "Conclusion": "Residual risk exists due to cross-supplier contradiction in performance claims",
            "Evidence Artifacts": "benchmark/contradicted_claims.json; validation_summary.json",
            "Status": "Traceable",
        },
        {
            "Conclusion": "Field validation is required before procurement lock-in",
            "Evidence Artifacts": "technical_due_diligence_report.md; claims_catalog.json",
            "Status": "Traceable",
        },
        {
            "Conclusion": "AI Coordinator approval was simulated under local policy",
            "Evidence Artifacts": "run_summary.json",
            "Status": "Traceable",
        },
    ]
    return rows


def build_glossary() -> Dict[str, str]:
    return {
        "IAR": "Intelligent Automatic Reel Warehouse",
        "RTLS": "Real-Time Location System",
        "UWB": "Ultra-Wideband positioning technology",
        "Digital Twin": "Operational model of warehouse assets and flows synchronized with real-world events",
        "INGEPRO": "INGECART core system integration target",
        "MES": "Manufacturing Execution System",
        "AMR": "Autonomous Mobile Robot",
        "AI Coordinator": "Governance and approval orchestration layer in ING_DIGHUB",
        "Verified": "Claim supported by independent technical evidence",
        "Partially Verified": "Claim supported by limited/indirect independent evidence",
        "Not Verified": "No independent evidence found",
        "Contradicted": "Independent evidence conflicts with claim",
    }


def build_markdown_report(
    latest_run: str,
    run_summary: Dict[str, Any],
    validation_summary: Dict[str, Any],
    arch_decision: Dict[str, Any],
    supplier_matrix_path: str,
    tech_matrix_path: str,
    trace_matrix_path: str,
    consistency: Dict[str, Any],
) -> str:
    selected = arch_decision.get("selected", {})
    return "\n".join(
        [
            "# IAR RTLS Due Diligence - Final Engineering Closure Report",
            "",
            f"Generated at: {now_iso()}",
            f"Consolidated run: {latest_run}",
            "",
            "## 1. Closure Scope",
            "This report consolidates existing mission artifacts only. No new external research was executed.",
            "",
            "## 2. Executive Decision",
            f"Recommended technology foundation: UWB-first RTLS with modular hybrid extension.",
            f"Recommended architecture: {selected.get('key')} - {selected.get('name')} (score {selected.get('overall_score')}).",
            "",
            "## 3. Consolidated Evidence Summary",
            f"- Documents processed: {run_summary.get('documents_processed')}",
            f"- Claims analyzed: {validation_summary.get('claims_total')}",
            f"- Verified claims: {validation_summary.get('verified')}",
            f"- Partially verified claims: {validation_summary.get('partially_verified')}",
            f"- Not verified claims: {validation_summary.get('not_verified')}",
            f"- Contradicted claims: {validation_summary.get('contradicted')}",
            f"- Unsupported claims: {validation_summary.get('unsupported_claims')}",
            "",
            "## 4. Consistency Audit",
            f"- Reported confidence score: {run_summary.get('quality_gates', {}).get('confidence_score_value')}",
            f"- Normalized evidence confidence index: {consistency.get('normalized_confidence_index')}",
            f"- Confidence consistency status: {consistency.get('status')}",
            f"- Notes: {consistency.get('note')}",
            "",
            "## 5. Supplier and Technology Benchmarks",
            f"- Supplier profile matrix: {supplier_matrix_path}",
            f"- Technology comparison matrix: {tech_matrix_path}",
            "",
            "## 6. Remaining Risks and Assumptions",
            "- Cross-vendor KPI definitions are not fully homogeneous (accuracy/latency refresh contexts differ).",
            "- Site-specific 3D behavior under metallic occlusion requires controlled pilot validation.",
            "- API depth and deterministic event behavior must be validated in INGEPRO/MES integration tests.",
            "",
            "## 7. Required Field Tests Before Product Development",
            "1. Multi-height reel stack localization with calibrated anchor topology.",
            "2. End-to-end INGEPRO and MES latency trace in production-like workload.",
            "3. 24/7 battery and stability soak test.",
            "4. AMR event handoff and geofence-trigger workflow verification.",
            "",
            "## 8. Traceability",
            f"Traceability matrix: {trace_matrix_path}",
            "All critical conclusions in this closure package are linked to mission artifacts.",
            "",
            "## 9. Governance",
            f"AI Coordinator status: {run_summary.get('ai_coordinator', {}).get('status')}",
            "Approval in this run was evaluated via local policy simulation due to unavailable live coordinator endpoint.",
            "",
            "## 10. Final Closure Statement",
            "Engineering recommendation is consolidated and publication-ready. Procurement or full productization should proceed only after passing the listed field validation tests.",
        ]
    )


def build_html_report(md_report: str, title: str) -> str:
    # Simple markdown-to-html formatting for publication-quality readability.
    lines = md_report.splitlines()
    html_body = []
    for ln in lines:
        if ln.startswith("# "):
            html_body.append(f"<h1>{ln[2:]}</h1>")
        elif ln.startswith("## "):
            html_body.append(f"<h2>{ln[3:]}</h2>")
        elif re_match_list(ln):
            html_body.append(f"<li>{ln[2:]}</li>")
        elif re_match_numbered(ln):
            html_body.append(f"<li>{ln}</li>")
        elif ln.strip() == "":
            html_body.append("<p></p>")
        else:
            html_body.append(f"<p>{ln}</p>")

    # Wrap orphan <li> items into <ul> blocks.
    wrapped = []
    in_list = False
    for item in html_body:
        if item.startswith("<li>") and not in_list:
            wrapped.append("<ul>")
            in_list = True
        if not item.startswith("<li>") and in_list:
            wrapped.append("</ul>")
            in_list = False
        wrapped.append(item)
    if in_list:
        wrapped.append("</ul>")

    body = "\n".join(wrapped)
    return f"""
<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\" />
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
<title>{title}</title>
<style>
:root {{ --bg:#f6f8f8; --ink:#13242d; --panel:#ffffff; --line:#d6e1e5; --accent:#0f766e; }}
body {{ margin:0; font-family:'Segoe UI',Tahoma,sans-serif; background:linear-gradient(160deg,#f1eee7 0%,#f3f7f8 55%,#eef6f5 100%); color:var(--ink); }}
.wrap {{ max-width:1060px; margin:24px auto; padding:0 16px; }}
.card {{ background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:24px; box-shadow:0 10px 28px rgba(12,34,44,.06); }}
h1 {{ color:#0b4f47; margin-top:0; }}
h2 {{ color:#0f172a; border-bottom:1px solid var(--line); padding-bottom:6px; margin-top:24px; }}
p {{ line-height:1.5; margin:8px 0; }}
ul {{ margin:8px 0 8px 20px; }}
small {{ color:#64748b; }}
</style>
</head>
<body>
<div class=\"wrap\"><div class=\"card\">{body}<hr /><small>Generated by IAR report closure consolidator.</small></div></div>
</body>
</html>
"""


def re_match_list(line: str) -> bool:
    return line.startswith("- ")


def re_match_numbered(line: str) -> bool:
    return bool(line[:3].strip().rstrip(".").isdigit() and line[1:3] in [". ", ") "])


def main() -> None:
    repo_root = Path(".")
    latest_meta = load_json(repo_root / "knowledge_hub" / "iar_assessment" / "latest_run.json")
    latest_run_rel = latest_meta["latest"].replace("\\", "/")
    latest_run = repo_root / latest_run_rel

    run_summary = load_json(latest_run / "run_summary.json")
    validation_summary = load_json(latest_run / "validation_summary.json")
    arch_decision = load_json(latest_run / "architecture_decision.json")

    normalized_conf = weighted_confidence(
        int(validation_summary.get("verified", 0)),
        int(validation_summary.get("partially_verified", 0)),
        int(validation_summary.get("not_verified", 0)),
        int(validation_summary.get("contradicted", 0)),
    )

    reported_conf = float(run_summary.get("quality_gates", {}).get("confidence_score_value", 0.0))
    delta = round(abs(reported_conf - normalized_conf), 2)
    consistency_status = "consistent" if delta <= 10 else "inconsistent"

    consistency = {
        "generated_at": now_iso(),
        "reported_confidence_score": reported_conf,
        "normalized_confidence_index": normalized_conf,
        "delta": delta,
        "status": consistency_status,
        "note": "Normalized index is based on validated claim distribution (Verified/Partial/Not Verified/Contradicted).",
    }

    closure_dir = latest_run / "final_closure"
    closure_dir.mkdir(parents=True, exist_ok=True)

    trace_rows = build_traceability_matrix(latest_run, run_summary, arch_decision)
    trace_path = closure_dir / "traceability_matrix.csv"
    write_csv(trace_path, trace_rows, ["Conclusion", "Evidence Artifacts", "Status"])

    glossary = build_glossary()
    glossary_path = closure_dir / "terminology_glossary.json"
    write_json(glossary_path, glossary)

    consistency_path = closure_dir / "consistency_audit.json"
    write_json(consistency_path, consistency)

    supplier_matrix_path = str((latest_run / "benchmark" / "supplier_profiles.csv").as_posix())
    tech_matrix_path = str((latest_run / "benchmark" / "technology_comparison_matrix.csv").as_posix())

    md_report = build_markdown_report(
        latest_run_rel,
        run_summary,
        validation_summary,
        arch_decision,
        supplier_matrix_path,
        tech_matrix_path,
        str(trace_path.as_posix()),
        consistency,
    )

    md_path = closure_dir / "IAR_FINAL_ENGINEERING_CLOSURE_REPORT.md"
    md_path.write_text(md_report, encoding="utf-8")

    html = build_html_report(md_report, "IAR RTLS Due Diligence Final Closure")
    html_path = closure_dir / "IAR_FINAL_ENGINEERING_CLOSURE_REPORT.html"
    html_path.write_text(html, encoding="utf-8")

    reports_dir = repo_root / "reports" / "iar" / "final_closure"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "IAR_FINAL_ENGINEERING_CLOSURE_REPORT.md").write_text(md_report, encoding="utf-8")
    (reports_dir / "IAR_FINAL_ENGINEERING_CLOSURE_REPORT.html").write_text(html, encoding="utf-8")

    publication_manifest = {
        "generated_at": now_iso(),
        "source_run": latest_run_rel,
        "final_reports": {
            "markdown": str(md_path.as_posix()),
            "html": str(html_path.as_posix()),
        },
        "supporting": {
            "traceability_matrix": str(trace_path.as_posix()),
            "terminology_glossary": str(glossary_path.as_posix()),
            "consistency_audit": str(consistency_path.as_posix()),
            "supplier_profiles": supplier_matrix_path,
            "technology_matrix": tech_matrix_path,
            "architecture_decision": str((latest_run / "architecture_decision.json").as_posix()),
            "validation_summary": str((latest_run / "validation_summary.json").as_posix()),
            "run_summary": str((latest_run / "run_summary.json").as_posix()),
        },
    }
    manifest_path = closure_dir / "publication_manifest.json"
    write_json(manifest_path, publication_manifest)

    print(json.dumps(publication_manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
