"""Genera un informe Markdown compacto a partir de los JSON en data/benchmarks.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict


def safe_get(d: Dict, *keys, default=None):
    cur = d
    for k in keys:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur


def summarize_benchmark_file(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    summary = {}
    # shape 1: top-level 'configs'
    if isinstance(data, dict) and "configs" in data:
        for name, cfg in data["configs"].items():
            meanA = safe_get(cfg, "mean_A", "meters_produced") or safe_get(cfg, "mean_A", "meters_produced")
            # fallback to mean_A.meters_produced or mean_A["meters_produced"]
            a = safe_get(cfg, "mean_A", "meters_produced", default=None)
            b = safe_get(cfg, "mean_B", "meters_produced", default=None)
            extra = None
            if a is not None and b is not None:
                extra = float(b) - float(a)
            payback = safe_get(cfg, "roi", "payback_years", default=None)
            summary[name] = {"A_meters": a, "B_meters": b, "extra_meters": extra, "payback": payback}
        return summary

    # shape 2: experiments -> summary
    if isinstance(data, dict):
        for name, v in data.items():
            if name.startswith("_"):
                continue
            # try expected structure from bottleneck_experiments
            s = safe_get(v, "summary")
            if s:
                a = safe_get(s, "meters", "A_mean")
                b = safe_get(s, "meters", "B_mean")
                summary[name] = {"A_meters": a, "B_meters": b, "extra_meters": (float(b) - float(a) if a is not None and b is not None else None), "payback": None}
        if summary:
            return summary

    # fallback: try to parse runs
    return {}


def main():
    bench_dir = Path("data") / "benchmarks"
    out_dir = Path("reports")
    out_dir.mkdir(exist_ok=True)
    report_md = out_dir / "validation_report.md"

    files = list(bench_dir.glob("*.json"))
    parts = ["# Validation report\n"]
    for f in sorted(files):
        parts.append(f"## {f.name}\n")
        try:
            summary = summarize_benchmark_file(f)
            if not summary:
                parts.append("No summary data parsed.\n")
                continue
            parts.append("| Config | A meters | B meters | Extra meters | Payback (years) |\n")
            parts.append("|---|---:|---:|---:|---:|\n")
            for name, s in summary.items():
                a = s.get("A_meters")
                b = s.get("B_meters")
                extra = s.get("extra_meters")
                payback = s.get("payback")
                parts.append(f"| {name} | {a if a is not None else '-'} | {b if b is not None else '-'} | {extra if extra is not None else '-'} | {payback if payback is not None else '-'} |\n")
        except Exception as e:
            parts.append(f"Error parsing {f.name}: {e}\n")

    report_md.write_text("\n".join(parts), encoding="utf-8")
    print(f"Wrote validation report to: {report_md}")


if __name__ == "__main__":
    main()
