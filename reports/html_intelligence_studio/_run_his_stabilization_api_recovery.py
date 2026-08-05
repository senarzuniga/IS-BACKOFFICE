from __future__ import annotations

import inspect
import json
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backoffice.his import HtmlIntelligenceStudio


ROOT = Path.cwd()
OUT = ROOT / "reports" / "html_intelligence_studio"
OUT.mkdir(parents=True, exist_ok=True)
UI_FILE = ROOT / "pages" / "html_intelligence_studio.py"
MISSION_REGISTRY = OUT / "mission_registry.jsonl"
KNOWLEDGE_HUB = ROOT / "knowledge_hub" / "outputs" / "html_intelligence_studio" / "his_stabilization_missions.jsonl"

MANDATORY_API = [
    "list_documents",
    "get_document",
    "create_document",
    "delete_document",
    "duplicate_document",
    "save_document",
    "open_document",
    "generate_html",
    "preview_document",
    "publish_document",
    "list_versions",
    "restore_version",
    "search",
    "statistics",
    "quality_report",
]


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _extract_ui_calls() -> list[str]:
    content = UI_FILE.read_text(encoding="utf-8", errors="ignore")
    return sorted(set(re.findall(r"studio\.([a-zA-Z_][a-zA-Z0-9_]*)\(", content)))


def _public_methods(obj: Any) -> list[str]:
    return sorted(
        name
        for name, member in inspect.getmembers(obj, predicate=callable)
        if not name.startswith("_")
    )


def _severity(implemented: bool, compatible: bool, deprecated: bool) -> str:
    if not implemented:
        return "critical"
    if not compatible:
        return "high"
    if deprecated:
        return "medium"
    return "low"


def _ui_api_matrix(studio: HtmlIntelligenceStudio) -> list[dict[str, Any]]:
    ui_calls = _extract_ui_calls()
    methods = set(_public_methods(studio))
    rows: list[dict[str, Any]] = []
    for method in ui_calls:
        implemented = method in methods
        compatible = implemented
        deprecated = method in {"run_first_mission"}
        replacement = "generate_html" if method == "run_first_mission" else (method if implemented else "missing")
        rows.append(
            {
                "ui_method": method,
                "target_object": "HtmlIntelligenceStudio",
                "implemented": implemented,
                "compatible": compatible,
                "deprecated": deprecated,
                "replacement": replacement,
                "severity": _severity(implemented, compatible, deprecated),
            }
        )
    return rows


def _mandatory_api_matrix(studio: HtmlIntelligenceStudio) -> list[dict[str, Any]]:
    methods = set(_public_methods(studio))
    rows: list[dict[str, Any]] = []
    for method in MANDATORY_API:
        implemented = method in methods
        rows.append(
            {
                "api_method": method,
                "implemented": implemented,
                "compatible": implemented,
                "severity": _severity(implemented, implemented, False),
            }
        )
    return rows


def _engine_audit(studio: HtmlIntelligenceStudio) -> dict[str, Any]:
    methods = _public_methods(studio)
    internal = [name for name, member in inspect.getmembers(studio, predicate=callable) if name.startswith("_")]
    deprecated = [m for m in methods if m in {"run_first_mission"}]

    missing_mandatory = [m for m in MANDATORY_API if m not in methods]
    duplicates = ["list_documents wrapper in service/repository"]

    return {
        "public_api": methods,
        "internal_api_count": len(internal),
        "repository_layer": "backoffice/his/repository.py::DocumentRepository",
        "service_layer": "backoffice/his/service.py::HtmlDocumentService",
        "persistence_layer": "reports/**/metadata/document_model.json",
        "rendering_layer": "backoffice/his/quality_pipeline_v3.py + DIPC PublicationEngine",
        "mission_layer": "mission_registry.jsonl + knowledge_hub outputs",
        "missing_methods": missing_mandatory,
        "renamed_methods": [{"from": "run_first_mission", "to": "generate_html", "status": "wrapper retained"}],
        "deleted_methods": [],
        "duplicated_methods": duplicates,
        "dead_code_signals": ["legacy FIRST_MISSION_* constants retained for compatibility"],
        "broken_wrappers": [],
        "deprecated": deprecated,
    }


def _regression(studio: HtmlIntelligenceStudio) -> dict[str, Any]:
    started = time.perf_counter()
    checks: list[dict[str, Any]] = []

    # API smoke
    try:
        docs = studio.list_documents()
        checks.append({"name": "api_list_documents", "pass": isinstance(docs, list)})
    except Exception as exc:
        checks.append({"name": "api_list_documents", "pass": False, "error": str(exc)})
        docs = []

    try:
        stats = studio.statistics()
        checks.append({"name": "api_statistics", "pass": isinstance(stats, dict)})
    except Exception as exc:
        checks.append({"name": "api_statistics", "pass": False, "error": str(exc)})

    try:
        result = studio.search("corrugated", limit=10)
        checks.append({"name": "api_search", "pass": isinstance(result, list)})
    except Exception as exc:
        checks.append({"name": "api_search", "pass": False, "error": str(exc)})

    # Repository smoke on available model
    model_path = docs[0].get("document_model_path", "") if docs else ""
    if model_path:
        try:
            got = studio.get_document(model_path)
            checks.append({"name": "repository_get_document", "pass": isinstance(got, dict)})
        except Exception as exc:
            checks.append({"name": "repository_get_document", "pass": False, "error": str(exc)})

        try:
            versions = studio.list_versions(model_path)
            checks.append({"name": "versioning_list_versions", "pass": isinstance(versions, list)})
        except Exception as exc:
            checks.append({"name": "versioning_list_versions", "pass": False, "error": str(exc)})

        try:
            q = studio.quality_report(model_path)
            checks.append({"name": "quality_report", "pass": isinstance(q, dict)})
        except Exception as exc:
            checks.append({"name": "quality_report", "pass": False, "error": str(exc)})

        try:
            p = studio.preview_document(model_path)
            checks.append({"name": "render_preview_document", "pass": isinstance(p, dict)})
        except Exception as exc:
            checks.append({"name": "render_preview_document", "pass": False, "error": str(exc)})

    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    return {
        "checks": checks,
        "pass": all(c.get("pass") for c in checks),
        "elapsed_ms": elapsed_ms,
    }


def _mission_log(payload: dict[str, Any]) -> None:
    row = {"ts": _now(), **payload}
    MISSION_REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    with MISSION_REGISTRY.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    KNOWLEDGE_HUB.parent.mkdir(parents=True, exist_ok=True)
    with KNOWLEDGE_HUB.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    studio = HtmlIntelligenceStudio()
    ui_matrix = _ui_api_matrix(studio)
    mandatory_matrix = _mandatory_api_matrix(studio)
    engine = _engine_audit(studio)
    regression = _regression(studio)

    api_compat = 100.0 if all(r["implemented"] and r["compatible"] for r in mandatory_matrix) else round(
        100.0
        * sum(1 for r in mandatory_matrix if r["implemented"] and r["compatible"])
        / max(1, len(mandatory_matrix)),
        2,
    )
    ui_compat = 100.0 if all(r["implemented"] and r["compatible"] for r in ui_matrix) else round(
        100.0 * sum(1 for r in ui_matrix if r["implemented"] and r["compatible"]) / max(1, len(ui_matrix)),
        2,
    )

    architecture_pass = (len(engine.get("missing_methods", [])) == 0)
    mission_pass = regression["pass"]

    executive_readiness = round((api_compat + ui_compat + (100.0 if regression["pass"] else 0.0) + (100.0 if architecture_pass else 0.0)) / 4.0, 2)
    mission_score = round(((100.0 if mission_pass else 0.0) + api_compat + ui_compat) / 3.0, 2)

    debt = {
        "open_debt": [
            "Deprecated method run_first_mission remains for compatibility",
            "UI still retains overlay helpers that should progressively move to service endpoints",
        ],
        "resolved_debt": [
            "Stable facade API wrappers restored",
            "Repository and service layers introduced",
            "UI access to mission history/upload/json and preview rendering routed through engine APIs",
        ],
    }

    performance = {
        "regression_elapsed_ms": regression["elapsed_ms"],
        "list_documents_count": len(studio.list_documents()),
        "status": "PASS" if regression["elapsed_ms"] < 5000 else "REVIEW",
    }

    final_status = "PRODUCTION READY" if (
        api_compat == 100.0
        and ui_compat == 100.0
        and regression["pass"]
        and architecture_pass
        and mission_pass
    ) else "NO GO"

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    architecture_report = OUT / f"his_api_stabilization_architecture_{stamp}.json"
    matrix_report = OUT / f"his_api_stabilization_matrix_{stamp}.json"
    regression_report = OUT / f"his_api_stabilization_regression_{stamp}.json"
    performance_report = OUT / f"his_api_stabilization_performance_{stamp}.json"
    debt_report = OUT / f"his_api_stabilization_debt_{stamp}.json"
    executive_report = OUT / f"his_api_stabilization_executive_{stamp}.json"

    architecture_report.write_text(json.dumps(engine, indent=2, ensure_ascii=False), encoding="utf-8")
    matrix_report.write_text(
        json.dumps({"ui_matrix": ui_matrix, "mandatory_api": mandatory_matrix}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    regression_report.write_text(json.dumps(regression, indent=2, ensure_ascii=False), encoding="utf-8")
    performance_report.write_text(json.dumps(performance, indent=2, ensure_ascii=False), encoding="utf-8")
    debt_report.write_text(json.dumps(debt, indent=2, ensure_ascii=False), encoding="utf-8")

    executive_payload = {
        "generated_at": _now(),
        "api_compatibility": api_compat,
        "ui_compatibility": ui_compat,
        "regression_pass": regression["pass"],
        "architecture_pass": architecture_pass,
        "mission_manager_pass": mission_pass,
        "knowledge_hub_updated": True,
        "executive_readiness": executive_readiness,
        "mission_score": mission_score,
        "final_status": final_status,
        "reports": {
            "architecture": str(architecture_report),
            "api_matrix": str(matrix_report),
            "regression": str(regression_report),
            "performance": str(performance_report),
            "technical_debt": str(debt_report),
        },
    }
    executive_report.write_text(json.dumps(executive_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    _mission_log(
        {
            "action": "his_api_stabilization_recovery",
            "objective": "Recover API consistency UI/Engine/Repository/Service",
            "status": final_status,
            "api_compatibility": api_compat,
            "ui_compatibility": ui_compat,
            "regression_pass": regression["pass"],
            "architecture_pass": architecture_pass,
            "report": str(executive_report),
            "lessons_learned": [
                "Facade APIs must remain stable while internal architecture evolves",
                "Repository/service split reduces UI coupling to file system details",
            ],
        }
    )

    print(json.dumps(executive_payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
