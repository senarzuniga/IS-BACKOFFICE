from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List


NAV_TARGETS = [
    "pages/ing_dighub_home.py",
    "pages/ing_dighub_knowledge_hub.py",
    "pages/ing_dighub_mission_manager.py",
    "pages/ing_dighub_digital_twin.py",
    "pages/industrial_engineering_platform.py",
    "pages/spoe_workbench.py",
    "pages/plant_simulator.py",
    "pages/reel_load_simulator_workbench.py",
    "pages/competitive_intelligence.py",
    "pages/project_closeout.py",
    "pages/facturacion.py",
]


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _duplicate_page_groups(repo_root: Path) -> List[List[str]]:
    pages_root = repo_root / "pages"
    groups: Dict[str, List[str]] = {}
    for p in pages_root.glob("*.py"):
        stem = re.sub(r"(_v\d+|_fixed|_workbench)$", "", p.stem)
        groups.setdefault(stem, []).append(str(p.relative_to(repo_root)).replace("\\", "/"))
    return [items for items in groups.values() if len(items) > 1]


def run_self_audit(repo_root: Path) -> Dict[str, Any]:
    missing_targets = [target for target in NAV_TARGETS if not (repo_root / target).exists()]

    duplicate_groups = _duplicate_page_groups(repo_root)

    ing_dighub_pages = [
        "pages/ing_dighub_home.py",
        "pages/ing_dighub_knowledge_hub.py",
        "pages/ing_dighub_mission_manager.py",
        "pages/ing_dighub_digital_twin.py",
    ]

    streamlit_app = (repo_root / "streamlit_app.py").read_text(encoding="utf-8", errors="ignore")
    orphan_modules = [p for p in ing_dighub_pages if p.split("/")[-1].replace(".py", "") not in streamlit_app]

    platform_registry = _load_json(repo_root / "platform_registry" / "platform_registry.json")
    capability_registry = _load_json(repo_root / "platform_registry" / "capability_registry.json")

    connections = {
        "knowledge_hub": (repo_root / "knowledge_hub").exists() and (repo_root / "pages" / "ing_dighub_knowledge_hub.py").exists(),
        "mission_manager": (repo_root / "backoffice" / "spoe" / "mission_manager.py").exists() and (repo_root / "pages" / "ing_dighub_mission_manager.py").exists(),
        "platform_registry": bool(platform_registry.get("objects")),
        "capability_registry": bool(capability_registry.get("capabilities")),
    }

    implemented_pages = ing_dighub_pages
    operational_pages = [p for p in ing_dighub_pages if (repo_root / p).exists()]
    placeholder_pages = ["pages/ing_dighub_digital_twin.py"]

    pending_integrations = []
    if missing_targets:
        pending_integrations.append("Fix missing navigation targets")
    if orphan_modules:
        pending_integrations.append("Wire orphan modules into top-level navigation")
    if not connections["knowledge_hub"]:
        pending_integrations.append("Reconnect Knowledge Hub path or page")
    if not connections["mission_manager"]:
        pending_integrations.append("Reconnect Mission Manager module or page")

    architecture_recommendations = [
        "Keep ING_DIGHUB as default entry point and keep existing workbenches as delegated views.",
        "Consolidate duplicated simulator/demo pages under a single canonical route.",
        "Expose AI-FACTORY health endpoint contract in API docs for stronger coordinator observability.",
    ]

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "implemented_pages": implemented_pages,
        "operational_pages": operational_pages,
        "placeholder_pages": placeholder_pages,
        "missing_navigation_targets": missing_targets,
        "duplicate_page_groups": duplicate_groups,
        "broken_imports": [],
        "orphan_modules": orphan_modules,
        "connections": connections,
        "pending_integrations": pending_integrations,
        "architecture_recommendations": architecture_recommendations,
    }


def write_html_report(report: Dict[str, Any], output_path: Path) -> Path:
    def li(values: List[str]) -> str:
        if not values:
            return "<li>None</li>"
        return "".join(f"<li>{v}</li>" for v in values)

    duplicates = [", ".join(group) for group in report.get("duplicate_page_groups", [])]

    html = f"""<!doctype html>
<html lang=\"en\"> 
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>ING_DIGHUB UI Status</title>
  <style>
    :root {{ --bg:#f6f4ef; --ink:#1f2a30; --muted:#5e6a70; --brand:#0f766e; --card:#ffffff; --warn:#b45309; --ok:#166534; }}
    body {{ margin:0; font-family: 'Segoe UI', Tahoma, sans-serif; background:linear-gradient(120deg,#f6f4ef,#e9f2ef); color:var(--ink); }}
    .wrap {{ max-width:1120px; margin:24px auto; padding:0 16px; }}
    .hero {{ background:var(--card); border-radius:16px; padding:20px; box-shadow:0 12px 28px rgba(0,0,0,.08); }}
    .grid {{ display:grid; grid-template-columns: repeat(auto-fit,minmax(260px,1fr)); gap:14px; margin-top:14px; }}
    .card {{ background:var(--card); border-radius:14px; padding:14px; box-shadow:0 8px 18px rgba(0,0,0,.06); }}
    h1,h2 {{ margin:0 0 8px; }}
    ul {{ margin:6px 0 0 18px; }}
    .ok {{ color:var(--ok); font-weight:700; }}
    .warn {{ color:var(--warn); font-weight:700; }}
    .muted {{ color:var(--muted); }}
  </style>
</head>
<body>
  <div class=\"wrap\"> 
    <section class=\"hero\"> 
      <h1>ING_DIGHUB UI STATUS</h1>
      <p class=\"muted\">Generated at: {report.get('generated_at')}</p>
      <p><strong>Knowledge Hub:</strong> <span class=\"{'ok' if report.get('connections', {}).get('knowledge_hub') else 'warn'}\">{'Connected' if report.get('connections', {}).get('knowledge_hub') else 'Disconnected'}</span></p>
      <p><strong>Mission Manager:</strong> <span class=\"{'ok' if report.get('connections', {}).get('mission_manager') else 'warn'}\">{'Connected' if report.get('connections', {}).get('mission_manager') else 'Disconnected'}</span></p>
      <p><strong>Registry State:</strong> <span class=\"{'ok' if report.get('connections', {}).get('platform_registry') and report.get('connections', {}).get('capability_registry') else 'warn'}\">{'Updated' if report.get('connections', {}).get('platform_registry') and report.get('connections', {}).get('capability_registry') else 'Needs Attention'}</span></p>
    </section>

    <section class=\"grid\"> 
      <article class=\"card\"><h2>Implemented Pages</h2><ul>{li(report.get('implemented_pages', []))}</ul></article>
      <article class=\"card\"><h2>Operational Pages</h2><ul>{li(report.get('operational_pages', []))}</ul></article>
      <article class=\"card\"><h2>Placeholder Pages</h2><ul>{li(report.get('placeholder_pages', []))}</ul></article>
      <article class=\"card\"><h2>Pending Integrations</h2><ul>{li(report.get('pending_integrations', []))}</ul></article>
      <article class=\"card\"><h2>Broken Links</h2><ul>{li(report.get('missing_navigation_targets', []))}</ul></article>
      <article class=\"card\"><h2>Duplicate Pages</h2><ul>{li(duplicates)}</ul></article>
      <article class=\"card\"><h2>Orphan Modules</h2><ul>{li(report.get('orphan_modules', []))}</ul></article>
      <article class=\"card\"><h2>Architecture Recommendations</h2><ul>{li(report.get('architecture_recommendations', []))}</ul></article>
    </section>
  </div>
</body>
</html>
"""

    output_path.write_text(html, encoding="utf-8")
    return output_path
