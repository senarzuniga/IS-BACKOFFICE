from __future__ import annotations

import inspect
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
UI_FILE = ROOT / "pages" / "html_intelligence_studio.py"
OUT_DIR = ROOT / "reports" / "html_intelligence_studio"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _public_methods(obj: Any) -> list[str]:
    return sorted([name for name in dir(obj) if not name.startswith("_")])


def _find_duplicates() -> dict[str, Any]:
    studio_files = [str(p.resolve()) for p in ROOT.glob("**/studio.py")]
    class_hits: list[dict[str, Any]] = []
    for py in ROOT.glob("**/*.py"):
        try:
            txt = py.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if re.search(r"class\s+HtmlIntelligenceStudio\b", txt):
            class_hits.append({"file": str(py.resolve()), "symbol": "class HtmlIntelligenceStudio"})
    return {
        "studio_py_files": studio_files,
        "html_intelligence_studio_classes": class_hits,
    }


def _pycache_inventory() -> dict[str, Any]:
    dirs = [p for p in ROOT.glob("**/__pycache__") if p.is_dir()]
    his_related = [str(p.resolve()) for p in dirs if "his" in str(p).lower() or "html_intelligence_studio" in str(p).lower()]
    return {
        "total_pycache_dirs": len(dirs),
        "his_related_pycache_dirs": his_related,
    }


def _pythonpath_conflicts() -> dict[str, Any]:
    import os
    import sys

    sys_path = [str(Path(p).resolve()) if p else "" for p in sys.path]
    backoffice_hits = [p for p in sys_path if p and (Path(p) / "backoffice").exists()]
    return {
        "pythonpath_env": os.environ.get("PYTHONPATH", ""),
        "sys_path_head": sys_path[:15],
        "backoffice_candidates_in_sys_path": backoffice_hits,
        "conflict_detected": len(backoffice_hits) > 1,
    }


def _ui_import_line() -> str:
    text = UI_FILE.read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines():
        if "HtmlIntelligenceStudio" in line and "import" in line:
            return line.strip()
    return ""


def main() -> None:
    from backoffice.his import HtmlIntelligenceStudio
    import pages.html_intelligence_studio as ui_module

    studio = HtmlIntelligenceStudio()
    methods = _public_methods(studio)

    imported_studio_file = str(Path(inspect.getfile(HtmlIntelligenceStudio)).resolve())
    imported_ui_file = str(Path(ui_module.__file__).resolve())

    ui_import = _ui_import_line()
    expected_import = "from backoffice.his import HtmlIntelligenceStudio"
    using_official_v3_import = ui_import == expected_import

    list_documents_exists = hasattr(studio, "list_documents") and callable(getattr(studio, "list_documents"))
    list_documents_call_ok = False
    list_documents_error = ""
    try:
        _ = studio.list_documents()
        list_documents_call_ok = True
    except Exception as exc:
        list_documents_error = str(exc)

    duplicates = _find_duplicates()
    pycache_info = _pycache_inventory()
    path_info = _pythonpath_conflicts()

    corrective_actions: list[str] = []
    if not using_official_v3_import:
        corrective_actions.append("UI import does not target official backoffice.his facade; correction required.")
    if path_info.get("conflict_detected"):
        corrective_actions.append("Multiple sys.path entries expose a backoffice package; import precedence should be reviewed.")

    report = {
        "generated_at": _now(),
        "mission": "HIS Runtime Module Resolution Audit",
        "requirements": {
            "studio_py_imported_absolute": imported_studio_file,
            "ui_file_absolute": imported_ui_file,
            "concrete_instantiated_class": f"{studio.__class__.__module__}.{studio.__class__.__name__}",
            "runtime_introspection": {
                "type_studio": str(type(studio)),
                "studio_class_module": studio.__class__.__module__,
                "inspect_getfile_html_intelligence_studio": imported_studio_file,
            },
            "public_methods_inventory": methods,
            "list_documents_exists": list_documents_exists,
            "list_documents_invocation_ok": list_documents_call_ok,
            "list_documents_error": list_documents_error,
            "duplicate_scan": duplicates,
            "pythonpath_pycache_conflicts": {
                "path": path_info,
                "pycache": pycache_info,
            },
        },
        "ui_import_resolution": {
            "ui_import_line": ui_import,
            "expected_import_line": expected_import,
            "using_official_v3_import": using_official_v3_import,
        },
        "corrective_actions": corrective_actions,
        "final_assertion": {
            "ui_invokes_list_documents_without_error": list_documents_exists and list_documents_call_ok,
            "ready": list_documents_exists and list_documents_call_ok and using_official_v3_import,
        },
    }

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = OUT_DIR / f"his_runtime_import_report_{stamp}.json"
    md_path = OUT_DIR / f"his_runtime_import_report_{stamp}.md"

    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    md_lines = [
        "# Runtime Import Report - HtmlIntelligenceStudio",
        f"- Generated: {report['generated_at']}",
        f"- studio.py imported: {imported_studio_file}",
        f"- UI file: {imported_ui_file}",
        f"- Concrete class: {report['requirements']['concrete_instantiated_class']}",
        f"- list_documents exists: {list_documents_exists}",
        f"- list_documents call OK: {list_documents_call_ok}",
        f"- Uses official V3 import: {using_official_v3_import}",
        f"- Final ready: {report['final_assertion']['ready']}",
    ]
    if corrective_actions:
        md_lines.append("## Corrective Actions")
        md_lines.extend([f"- {a}" for a in corrective_actions])
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    print(json.dumps({
        "report_json": str(json_path),
        "report_md": str(md_path),
        "ready": report["final_assertion"]["ready"],
        "list_documents_ok": list_documents_call_ok,
        "using_official_v3_import": using_official_v3_import,
        "corrective_actions": corrective_actions,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
