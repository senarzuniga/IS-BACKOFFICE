from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def build_report(root: Path) -> dict:
    py_files = [
        path for path in root.rglob("*.py")
        if ".git" not in path.parts and ".venv" not in path.parts and "__pycache__" not in path.parts
    ]
    top_level = sorted(item.name for item in root.iterdir() if not item.name.startswith(".") or item.name in {".github", ".env.example"})
    by_folder = Counter()
    for path in py_files:
        relative = path.relative_to(root)
        folder = relative.parts[0] if len(relative.parts) > 1 else "."
        by_folder[folder] += 1

    module_summary = {
        key.replace("-", "_"): {"file_count": count, "path": f"{key}/" if key != "." else "."}
        for key, count in sorted(by_folder.items())
    }
    biggest = sorted(module_summary.items(), key=lambda item: item[1]["file_count"], reverse=True)[:5]
    biggest_summary = ", ".join(f"{name} ({meta['file_count']})" for name, meta in biggest)
    summary = (
        f"Architecture scan completed successfully. "
        f"Scanned {len(py_files)} Python files across {len(module_summary)} top-level areas. "
        f"Largest areas: {biggest_summary}."
    )

    return {
        "metadata": {
            "generated_by": "Copilot CLI architecture assistant",
            "date": datetime.now(timezone.utc).isoformat(),
            "repo_root": str(root),
        },
        "scanned_files": len(py_files),
        "summary": summary,
        "top_level_folders": top_level,
        "module_summary": module_summary,
        "findings": [],
        "recommendations": [
            "Review large top-level modules regularly to control architecture drift.",
            "Keep this report refreshed in CI to detect repository structure changes early.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate architecture scan report")
    parser.add_argument("--root", required=True, help="Repository root to scan")
    parser.add_argument("--report", required=True, help="Output JSON report path")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Root path not found: {root}")

    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = (root / report_path).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report = build_report(root)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(summary := report["summary"])
    print(f"Report written to: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
