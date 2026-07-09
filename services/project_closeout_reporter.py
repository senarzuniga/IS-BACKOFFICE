"""Reporter utilities for Project Closeout.

Generate a structured JSON export and a simple HTML closeout report.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Dict, Optional


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def generate_project_closeout_report(service, project_id: str, out_dir: Optional[str] = None) -> Dict[str, str]:
    out_root = out_dir or os.path.join("data", "project_closeout", "reports")
    _ensure_dir(out_root)

    project = service.get_project(project_id) or {}
    issues = service.get_issues_df(project_id)
    # issues may be list or pandas.DataFrame
    try:
        import pandas as pd

        if not isinstance(issues, pd.DataFrame):
            issues_df = pd.DataFrame(issues)
        else:
            issues_df = issues
    except Exception:
        # issues is a list
        issues_df = None

    payload = {
        "project": project,
        "issues_count": len(issues_df) if issues_df is not None else (len(issues) if isinstance(issues, list) else 0),
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }

    json_path = os.path.join(out_root, f"project_{project_id}.json")
    html_path = os.path.join(out_root, f"project_{project_id}.html")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # Build a simple HTML report
    html_lines = [
        "<html>",
        "<head><meta charset='utf-8'><title>Project Closeout Report</title>",
        "<style>body{font-family:Arial,Helvetica,sans-serif;background:#f7f9fb;color:#0f172a;padding:24px}h1{color:#0f172a}table{border-collapse:collapse;width:100%}th,td{padding:8px;border:1px solid #ddd}th{background:#0f172a;color:#fff}</style>",
        "</head>",
        "<body>",
        f"<h1>Project Closeout — {project.get('project_name', project_id)}</h1>",
        f"<p><strong>Project ID:</strong> {project.get('project_id', project_id)}</p>",
        f"<p><strong>Generated at:</strong> {payload['generated_at']}</p>",
        "<h2>Executive Summary</h2>",
        f"<pre>{json.dumps(project.get('master_data', {}), ensure_ascii=False, indent=2)}</pre>",
    ]

    if issues_df is not None and not issues_df.empty:
        try:
            issues_html = issues_df.to_html(index=False, classes="issues-table")
            html_lines.append("<h2>Punch List / Issues</h2>")
            html_lines.append(issues_html)
        except Exception:
            html_lines.append("<h2>Punch List / Issues</h2>")
            html_lines.append(f"<pre>{str(issues_df)}</pre>")

    html_lines.append("</body></html>")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html_lines))

    # Record version
    try:
        service._conn.execute("INSERT INTO report_versions (project_id, version, path_html, path_json, generated_at) VALUES (?, ?, ?, ?, ?)",
                              (project_id, datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"), os.path.relpath(html_path), os.path.relpath(json_path), datetime.utcnow().isoformat() + "Z"))
        service._conn.commit()
    except Exception:
        pass

    return {"html": html_path, "json": json_path}
