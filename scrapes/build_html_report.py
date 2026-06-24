#!/usr/bin/env python3
"""Build a standalone HTML report from scrapes/ingecart_proyectos/report.json

Embeds images as data URIs to make a single-file report.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Dict


def image_to_data_uri(img_path: Path) -> str:
    mime = "image/jpeg"
    if img_path.suffix.lower() == ".png":
        mime = "image/png"
    try:
        b = img_path.read_bytes()
        return f"data:{mime};base64,{base64.b64encode(b).decode('ascii')}"
    except Exception:
        return ""


def build(report_json: Path, out_html: Path):
    data = json.loads(report_json.read_text(encoding="utf-8"))

    title = data.get("title") or "Scrape Report"
    lines = []
    lines.append("<!doctype html>")
    lines.append("<html lang=\"en\">")
    lines.append("<head>")
    lines.append(f"<meta charset=\"utf-8\"><title>{title}</title>")
    # minimal styles
    lines.append("<style>body{font-family:Arial,Helvetica,sans-serif;margin:24px}h1,h2,h3{color:#1a1a1a}img{max-width:320px;height:auto;border:1px solid #ddd;padding:4px;margin:8px 0}</style>")
    lines.append("</head><body>")
    lines.append(f"<h1>{title}</h1>")
    lines.append(f"<p><strong>Source:</strong> <a href=\"{data.get('url')}\">{data.get('url')}</a></p>")

    if data.get("meta_description"):
        lines.append(f"<p><em>{data.get('meta_description')}</em></p>")

    # Regions and projects
    lines.append("<h2>Regions & Projects</h2>")
    for region in data.get("regions", []):
        lines.append(f"<h3>{region.get('region')}</h3>")
        for p in region.get("projects", []):
            lines.append(f"<h4>{p.get('title')}</h4>")
            # embed image if available
            img_local = p.get("image_local")
            if img_local:
                img_path = report_json.parent / "assets" / img_local
                data_uri = image_to_data_uri(img_path) if img_path.exists() else ""
                if data_uri:
                    lines.append(f"<img src=\"{data_uri}\" alt=\"{p.get('title')}\">")
            if p.get("description"):
                lines.append(f"<p>{p.get('description')}</p>")
            if p.get("link"):
                lines.append(f"<p><a href=\"{p.get('link')}\">Project link</a></p>")

    # partners
    partners = data.get("partners_local") or []
    if any(partners):
        lines.append("<h2>Partners</h2>")
        for pl in partners:
            if not pl:
                continue
            ppath = report_json.parent / "assets" / pl
            if not ppath.exists():
                continue
            data_uri = image_to_data_uri(ppath)
            if data_uri:
                lines.append(f"<img src=\"{data_uri}\" alt=\"partner\">")

    # numbers
    numbers = data.get("numbers") or {}
    if numbers:
        lines.append("<h2>Numbers</h2><ul>")
        for k, v in numbers.items():
            lines.append(f"<li><strong>{k or 'Metric'}:</strong> {v}</li>")
        lines.append("</ul>")

    # footer
    if data.get("footer"):
        lines.append("<h2>Contact & Footer</h2>")
        lines.append(f"<pre style=\"white-space:pre-wrap;\">{data.get('footer').get('text','')}</pre>")

    lines.append("</body></html>")

    out_html.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--report", default="scrapes/ingecart_proyectos/report.json")
    p.add_argument("--out", default="scrapes/ingecart_proyectos/report_standalone.html")
    args = p.parse_args()
    build(Path(args.report), Path(args.out))
