#!/usr/bin/env python3
"""
Backoffice Production Health Check
- Verifies presence of key modules, imports, assets, folders, and minimal operations.
- Writes BACKOFFICE_HEALTH_REPORT.md to repo root.

Run with the project's Python interpreter.
"""

from __future__ import annotations

import importlib
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = ROOT / "BACKOFFICE_HEALTH_REPORT.md"

checks = []


def add_check(name: str, ok: bool, detail: str = ""):
    checks.append({"name": name, "ok": bool(ok), "detail": str(detail)})


# 1. Files existence
modules_to_find = [
    "pages/facturacion.py",
    "pages/ingecart_artwork.py",
    "pages/ingecart_video_editor.py",
    "streamlit_app.py",
    "backoffice/ui/app.py",
]
for p in modules_to_find:
    fp = ROOT / p
    add_check(f"File exists: {p}", fp.exists(), f"Path: {fp}")

# 2. Try importing key Python packages used by modules
packages = [
    ("streamlit", "streamlit"),
    ("pandas", "pandas"),
    ("PIL", "PIL"),
    ("numpy", "numpy"),
    ("moviepy", "moviepy"),
    ("reportlab", "reportlab"),
    ("plotly", "plotly"),
    ("playwright.sync_api", "playwright.sync_api"),
]

for display, pkg in packages:
    try:
        mod = importlib.import_module(pkg)
        v = getattr(mod, "__version__", "?")
        add_check(f"Import {display}", True, f"version={v}")
    except Exception as exc:
        add_check(f"Import {display}", False, f"{type(exc).__name__}: {exc}")

# 3. ERP minimal check (init DB and ensure invoice dir)
try:
    import erp_facturacion.erp as erp
    try:
        erp.init_db()
        db_path = Path(erp.DB)
        invoice_dir = Path(erp.INVOICE_DIR)
        logo_dir = Path(erp.LOGO_DIR)
        add_check("ERP: init_db()", True, f"DB: {db_path} ; invoices: {invoice_dir} ; logos: {logo_dir}")
    except Exception as exc:
        add_check("ERP: init_db()", False, f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}" )
except Exception as exc:
    add_check("ERP module import", False, f"{type(exc).__name__}: {exc}")

# 4. Artwork component check (create a tiny image and render using Pillow fallback)
try:
    from backoffice.ui.components import artwork as artwork_mod
    try:
        ART_DIR = Path(artwork_mod.ARTWORK_OUTPUT_DIR)
        ART_DIR.mkdir(parents=True, exist_ok=True)
        # Create a tiny temp image
        tmp_src = ART_DIR / "_health_check_tmp.png"
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (400, 300), (200, 200, 200))
        d = ImageDraw.Draw(img)
        d.text((20, 20), "health check", fill=(0, 0, 0))
        img.save(tmp_src)
        out_png, out_html, msg = artwork_mod._generate_artwork(tmp_src, "health_check_artwork")
        add_check("Artwork generation (Pillow)", out_png.exists() and out_html.exists(), f"png={out_png} html={out_html} msg={msg}")
        # cleanup temp image
        try:
            tmp_src.unlink()
        except Exception:
            pass
    except Exception as exc:
        add_check("Artwork generation", False, f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}")
except Exception as exc:
    add_check("Artwork module import", False, f"{type(exc).__name__}: {exc}")

# 5. Video editor checks (constants and assets)
try:
    import pages.ingecart_video_editor as ved
    try:
        opening = Path(ved.OPENING_IMAGE_PATH)
        closing = Path(ved.CLOSING_IMAGE_PATH)
        outdir = Path(ved.OUTPUT_DIR)
        outdir_ok = outdir.exists() or (outdir.mkdir(parents=True, exist_ok=True) is None)
        add_check("Video editor module import", True, f"opening={opening.exists()} closing={closing.exists()} output_dir={outdir}")
    except Exception as exc:
        add_check("Video editor runtime check", False, f"{type(exc).__name__}: {exc}")
except Exception as exc:
    add_check("Video editor import", False, f"{type(exc).__name__}: {exc}")

# 6. Streamlit app entry resolution
try:
    import streamlit_app as sa
    try:
        resolver = getattr(sa, "_resolve_main", None)
        add_check("Streamlit app import", callable(resolver), f"_resolve_main callable: {callable(resolver)}")
    except Exception as exc:
        add_check("Streamlit app runtime", False, f"{type(exc).__name__}: {exc}")
except Exception as exc:
    add_check("Streamlit app import", False, f"{type(exc).__name__}: {exc}")

# 7. Templates & assets quick check
templates = [
    ROOT / "informes" / "ingecart-marketing-kit" / "Templates" / "ingecart_report_base.html",
    ROOT / "informes" / "PSC_VISALIA_EXECUTIVE_REPORT_2026-05-11.md",
]
for t in templates:
    add_check(f"Template exists: {t.name}", t.exists(), f"Path: {t}")

# 8. Requirements consistency: try reading requirements.txt
req_path = ROOT / "requirements.txt"
if req_path.exists():
    try:
        content = req_path.read_text(encoding="utf-8")
        add_check("requirements.txt present", True, f"{len(content.splitlines())} lines")
    except Exception as exc:
        add_check("requirements.txt read", False, f"{exc}")
else:
    add_check("requirements.txt present", False, "Not found")

# 9. Report generation
now = datetime.now().isoformat()
md_lines = [f"# BACKOFFICE HEALTH REPORT\n\nGenerated: {now}\n\n"]

ok_count = 0
for c in checks:
    status = "OK" if c["ok"] else "FAIL"
    if c["ok"]:
        ok_count += 1
    md_lines.append(f"- **{status}**: {c['name']} — {c['detail']}\n")

score = int(100 * ok_count / max(1, len(checks)))
md_lines.insert(1, f"\n**Summary**: {ok_count}/{len(checks)} checks passed — Health Score: {score}/100\n\n")

REPORT_PATH.write_text("\n".join(md_lines), encoding="utf-8")
print(repr(REPORT_PATH))
print("Health score:", score)

if score < 80:
    sys.exit(2)

sys.exit(0)
