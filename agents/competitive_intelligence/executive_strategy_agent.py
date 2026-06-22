import os
import datetime
from typing import Dict, Any, List


class ExecutiveStrategyAgent:
    def __init__(self):
        pass

    def run(self, company: str, profile: Dict[str, Any], benchmark: Dict[str, Any]) -> str:
        ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        reports_dir = os.path.join(root, "data", "competitive_intelligence", "reports")
        os.makedirs(reports_dir, exist_ok=True)
        out_path = os.path.join(reports_dir, f"{company}_{ts}.md")

        # Build a concise consultant-style report
        lines: List[str] = []
        lines.append(f"# {company} — Deep Strategic Report")
        lines.append(f"Generated: {ts} UTC")
        lines.append("\n## Executive Summary\n")
        summary = profile.get("description") or "No disponible en fuentes públicas"
        lines.append(summary)

        lines.append("\n## Profile\n")
        lines.append(f"**Products:** {', '.join(profile.get('products') or [])}")
        lines.append(f"**Markets:** {', '.join(profile.get('markets') or [])}")
        lines.append(f"**Estimated revenue:** {profile.get('estimated_revenue')}")

        lines.append("\n## Benchmark\n")
        lines.append(benchmark.get("markdown", ""))

        lines.append("\n## Recommendations\n")
        lines.append("1. Pilot Smart Plant project focusing on predictive maintenance and quick ROI.")
        lines.append("2. Build retrofit offering with clear payback case studies.")

        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))

        return out_path
