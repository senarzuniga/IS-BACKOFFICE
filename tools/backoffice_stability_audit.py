#!/usr/bin/env python3
"""
Backoffice Stability Audit
Performs import-time checks for key modules, asset existence checks, and Streamlit server availability.
Writes BACKOFFICE_STABILITY_AUDIT.md in the repo root.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

try:
    import requests
except Exception:
    requests = None

ROOT = Path(__file__).resolve().parents[1]
AUDIT_MD = ROOT / "BACKOFFICE_STABILITY_AUDIT.md"
PY = sys.executable

MODULE_CHECKS = [
    {"name": "Dashboard", "module": "backoffice.ui.command_center", "file": ROOT / "backoffice" / "ui" / "command_center.py"},
    {"name": "ERP", "module": "erp_facturacion.erp", "file": ROOT / "erp_facturacion" / "erp.py"},
    {"name": "Facturacion", "module": "pages.facturacion", "file": ROOT / "pages" / "facturacion.py"},
    {"name": "Artwork", "module": "pages.ingecart_artwork", "file": ROOT / "pages" / "ingecart_artwork.py"},
    {"name": "Video Editor", "module": "pages.ingecart_video_editor", "file": ROOT / "pages" / "ingecart_video_editor.py"},
]


def run_import_subprocess(mod_name: str, timeout: int = 30) -> dict:
    # Run import in a subprocess to isolate import-time failures
    code = (
        "import importlib, json, traceback\n"
        "res = {}\n"
        f"try:\n importlib.import_module('{mod_name}')\n res['ok'] = True\n"
        "except Exception as e:\n res['ok'] = False\n res['error'] = str(e)\n res['trace'] = traceback.format_exc()\n"
        "print(json.dumps(res))\n"
    )
    try:
        proc = subprocess.run([PY, "-c", code], capture_output=True, text=True, timeout=timeout)
        out = proc.stdout.strip()
        if not out:
            # fallback: include stderr
            out = proc.stderr.strip()
        try:
            return json.loads(out)
        except Exception:
            return {"ok": False, "error": "Invalid JSON from subprocess", "raw_stdout": out, "stderr": proc.stderr}
    except subprocess.TimeoutExpired as e:
        return {"ok": False, "error": "timeout", "trace": str(e)}
    except Exception as e:
        return {"ok": False, "error": str(e), "trace": traceback.format_exc()}


def parse_missing_deps(trace: str) -> list:
    missing = set()
    if not trace:
        return []
    # Find ModuleNotFoundError: No module named 'xyz'
    for m in re.finditer(r"ModuleNotFoundError: No module named '?([\w_.-]+)'?", trace):
        missing.add(m.group(1))
    # Also search for ImportError: No module named xyz
    for m in re.finditer(r"No module named '?([\w_.-]+)'?", trace):
        missing.add(m.group(1))
    return sorted(list(missing))


def check_assets_for_module(entry: dict) -> dict:
    name = entry['name']
    assets = []
    try:
        if name == 'Facturacion':
            db = ROOT / "erp_facturacion" / "database.db"
            inv = ROOT / "erp_facturacion" / "invoices"
            logos = ROOT / "erp_facturacion" / "logos"
            assets.append(("ERP DB", db.exists(), str(db)))
            assets.append(("Invoices dir", inv.exists(), str(inv)))
            assets.append(("Logos dir", logos.exists(), str(logos)))
        if name == 'Artwork':
            # import module to read ARTWORK_OUTPUT_DIR
            try:
                mod = __import__("backoffice.ui.components.artwork", fromlist=["*"])
                outdir = Path(mod.ARTWORK_OUTPUT_DIR)
                assets.append(("Artwork output dir", outdir.exists(), str(outdir)))
            except Exception as e:
                assets.append(("Artwork import for assets", False, str(e)))
        if name == 'Video Editor':
            try:
                mod = __import__("pages.ingecart_video_editor", fromlist=["*"])
                opening = Path(mod.OPENING_IMAGE_PATH)
                closing = Path(mod.CLOSING_IMAGE_PATH)
                outdir = Path(mod.OUTPUT_DIR)
                assets.append(("Opening image", opening.exists(), str(opening)))
                assets.append(("Closing image", closing.exists(), str(closing)))
                assets.append(("Video output dir", outdir.exists(), str(outdir)))
            except Exception as e:
                assets.append(("Video module asset check failed", False, str(e)))
    except Exception as e:
        assets.append(("Asset check error", False, str(e)))
    return {"assets": assets}


def check_streamlit_server(url: str = "http://localhost:8501") -> dict:
    if requests is None:
        return {"available": False, "note": "requests not installed in auditor environment"}
    try:
        r = requests.get(url, timeout=4)
        return {"available": True, "status_code": r.status_code, "ok": r.ok}
    except Exception as e:
        return {"available": False, "error": str(e)}


def main():
    results = {"generated_at": datetime.now().isoformat(), "modules": []}

    # Module checks
    for m in MODULE_CHECKS:
        row = {"name": m['name'], "module": m['module'], "file_exists": bool(m['file'].exists())}
        imp = run_import_subprocess(m['module'])
        row['import_ok'] = bool(imp.get('ok'))
        if not imp.get('ok'):
            row['error'] = imp.get('error')
            row['trace'] = imp.get('trace')
            row['missing_deps'] = parse_missing_deps(imp.get('trace') or imp.get('error') or '')
        # assets
        assets_res = check_assets_for_module(m)
        row.update(assets_res)

        results['modules'].append(row)

    # Streamlit server check
    server = check_streamlit_server()
    results['streamlit_server'] = server

    # Navigation check: ensure pages referenced in streamlit_app exist
    nav_checks = []
    try:
        app_py = ROOT / 'streamlit_app.py'
        content = app_py.read_text(encoding='utf-8')
        # find occurrences of switch_page("pages/...")
        pages = re.findall(r"switch_page\(\s*\"([^\"]+)\"\s*\)", content)
        pages = sorted(set(pages))
        for p in pages:
            path = ROOT / p
            nav_checks.append({"page": p, "exists": path.exists(), "path": str(path)})
    except Exception as e:
        nav_checks.append({"error": str(e)})
    results['navigation'] = nav_checks

    # Severity classification and pass/fail per module
    summary_lines = []
    ok_count = 0
    for r in results['modules']:
        problems = []
        if not r.get('file_exists'):
            problems.append('missing file')
        if not r.get('import_ok'):
            problems.append('import failure')
        for asset in r.get('assets', []):
            if not asset[1]:
                problems.append(f"asset missing: {asset[0]}")
        severity = 'OK' if not problems else ('CRITICAL' if any('import' in p or 'missing file' in p for p in problems) else 'WARN')
        status = 'PASS' if severity == 'OK' else 'FAIL'
        if status == 'PASS':
            ok_count += 1
        summary_lines.append({
            'module': r['name'],
            'status': status,
            'severity': severity,
            'problems': problems,
            'details': r
        })

    # Write markdown report
    lines = [f"# BACKOFFICE STABILITY AUDIT\n\nGenerated: {results['generated_at']}\n\n"]
    lines.append(f"## Summary: {ok_count}/{len(results['modules'])} modules passed basic checks\n\n")

    for s in summary_lines:
        lines.append(f"### {s['module']} — {s['status']} ({s['severity']})\n")
        if s['problems']:
            for p in s['problems']:
                lines.append(f"- **Problem:** {p}\n")
        # include errors/traces
        details = s['details']
        if not details.get('import_ok'):
            lines.append("- **Import Error**:\n\n```")
            lines.append(str(details.get('trace') or details.get('error') or ''))
            lines.append("```\n")
        # assets
        if details.get('assets'):
            lines.append("- **Assets**:\n")
            for a in details.get('assets'):
                lines.append(f"  - {a[0]}: {'OK' if a[1] else 'MISSING'} — {a[2]}\n")
        lines.append("\n")

    # Streamlit server
    lines.append("## Streamlit Server\n\n")
    if results['streamlit_server'].get('available'):
        lines.append(f"- Server reachable at http://localhost:8501 — status {results['streamlit_server'].get('status_code')}\n\n")
    else:
        lines.append(f"- Server NOT reachable — reason: {results['streamlit_server'].get('error') or results['streamlit_server'].get('note')}\n\n")

    # Navigation
    lines.append("## Navigation checks\n\n")
    for nav in results['navigation']:
        if 'error' in nav:
            lines.append(f"- Navigation parse error: {nav['error']}\n")
        else:
            lines.append(f"- Page {nav['page']}: {'OK' if nav['exists'] else 'MISSING'} — {nav['path']}\n")

    AUDIT_MD.write_text('\n'.join(lines), encoding='utf-8')
    print(str(AUDIT_MD))


if __name__ == '__main__':
    main()
