#!/usr/bin/env python3
"""Repository Discovery Engine

Scans the workspace and generates:
- platform_registry/platform_registry.json
- reports/reuse_map.json
- reports/platform_discovery_report.md

Heuristics are lightweight and intended to bootstrap the Platform Registry.
"""
from __future__ import annotations

import os
import re
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List

ROOT_EXCLUDES = {".git", ".venv", "venv", "node_modules", "__pycache__", "build", "dist"}

KEYWORDS = {
    "streamlit": [r"import\s+streamlit\s+as\s+st", r"streamlit\."],
    "fastapi": [r"from\s+fastapi", r"FastAPI\("],
    "flask": [r"from\s+flask", r"Flask\("],
    "agent": [r"class\s+\w*Agent", r"def\s+run_agent", r"agent_id"],
    "simulation": [r"simulate", r"simulation", r"Simulator", r"simulator"],
    "engine": [r"class\s+\w*Engine", r"Engine\("],
    "knowledge": [r"KnowledgeHub", r"Knowledge Hub", r"knowledge"],
    "workbench": [r"workbench", r"Workbench"],
    "ui": [r"react", r"render", r"Streamlit", r"Streamlit\b"],
}


def read_head(path: Path, limit: int = 4096) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            return f.read(limit)
    except Exception:
        return ""


def detect_categories(content: str, rel_path: str) -> List[str]:
    categories = set()
    low = content.lower()
    # path-based hints
    p = rel_path.lower()
    if "/agents/" in p or p.startswith("agents/"):
        categories.add("Agent")
    if "/pages/" in p or p.startswith("pages/"):
        categories.add("UI Component")
    if "/frontend/" in p:
        categories.add("UI Component")
    if "/services/" in p:
        categories.add("Service")
    if "/docs/" in p or rel_path.endswith(".md"):
        categories.add("Documentation")
    if "/tests/" in p or "/test_" in p:
        categories.add("Test")

    for k, patterns in KEYWORDS.items():
        for pat in patterns:
            if re.search(pat, content, flags=re.IGNORECASE):
                # map keyword to category
                if k == "streamlit":
                    categories.add("Workbench")
                elif k in ("fastapi", "flask"):
                    categories.add("API Service")
                elif k == "agent":
                    categories.add("Agent")
                elif k == "simulation":
                    categories.add("Simulation")
                elif k == "engine":
                    categories.add("Engine")
                elif k == "knowledge":
                    categories.add("Knowledge Source")
                elif k == "workbench":
                    categories.add("Workbench")
                elif k == "ui":
                    categories.add("UI Component")
                break

    # fallback
    if not categories:
        if rel_path.endswith(".py"):
            categories.add("Module")
        else:
            categories.add("Other")

    return sorted(categories)


def extract_description(content: str) -> str:
    # try module docstring
    m = re.search(r"^\s*[ru]*\"\"\"(.*?)(\"\"\"|$)", content, flags=re.S | re.I)
    if m:
        desc = m.group(1).strip().splitlines()[0:3]
        return " ".join([line.strip() for line in desc]).strip()
    # fallback: first non-empty comment or first line
    for line in content.splitlines():
        s = line.strip()
        if s.startswith("#"):
            return s.lstrip("# ")[:200]
        if s:
            return s[:200]
    return ""


def walk_and_discover(root: Path) -> List[Dict]:
    objects = []
    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        # prune excluded dirs
        parts = Path(dirpath).parts
        if any(p in ROOT_EXCLUDES for p in parts):
            continue
        for name in filenames:
            fpath = Path(dirpath) / name
            rel = str(fpath.relative_to(root)).replace("\\", "/")
            # skip large/binary
            if name.endswith(('.pyc', '.pkl', '.jpg', '.png', '.exe', '.dll')):
                continue
            content = read_head(fpath, limit=8192)
            cats = detect_categories(content, rel)
            desc = extract_description(content)
            obj = {
                "id": str(uuid.uuid4()),
                "name": name,
                "path": rel,
                "categories": cats,
                "description": desc,
                "owner": None,
                "status": "discovered",
                "version": None,
                "has_tests": ("tests/" in rel or rel.startswith("tests/")),
                "detected_at": datetime.utcnow().isoformat() + "Z",
            }
            objects.append(obj)
    return objects


def summarize(objects: List[Dict]) -> Dict:
    by_cat = {}
    for o in objects:
        for c in o["categories"]:
            by_cat.setdefault(c, 0)
            by_cat[c] += 1
    return {"total_objects": len(objects), "by_category": by_cat}


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_report(path: Path, summary: Dict, objects: List[Dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(f"# Platform Discovery Report\n\n")
        f.write(f"Generated: {datetime.utcnow().isoformat()}Z\n\n")
        f.write(f"- Total discovered objects: {summary['total_objects']}\n")
        f.write(f"- Categories:\n")
        for k, v in sorted(summary["by_category"].items(), key=lambda x: -x[1]):
            f.write(f"  - {k}: {v}\n")
        f.write("\n## Sample Objects (first 50)\n\n")
        for o in objects[:50]:
            f.write(f"- **{o['name']}** — `{o['path']}` — {', '.join(o['categories'])}\n")


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Repository root to scan")
    parser.add_argument("--out-dir", default="platform_registry", help="Output directory for registry files")
    args = parser.parse_args()

    root = Path(args.root)
    print(f"Scanning repository root: {root.resolve()}")
    objects = walk_and_discover(root)

    summary = summarize(objects)

    out_dir = Path(args.out_dir)
    registry_file = out_dir / "platform_registry.json"
    reuse_map_file = Path("reports") / "reuse_map.json"
    report_file = Path("reports") / "platform_discovery_report.md"

    save_json(registry_file, {"generated_at": datetime.utcnow().isoformat() + "Z", "objects": objects, "summary": summary})
    save_json(reuse_map_file, {"generated_at": datetime.utcnow().isoformat() + "Z", "objects": objects})
    write_report(report_file, summary, objects)

    print("Discovery complete.")
    print(f"Objects discovered: {summary['total_objects']}")
    for k, v in summary["by_category"].items():
        print(f"  {k}: {v}")
    print(f"Registry written to: {registry_file}")
    print(f"Reuse map written to: {reuse_map_file}")
    print(f"Report written to: {report_file}")


if __name__ == "__main__":
    main()
