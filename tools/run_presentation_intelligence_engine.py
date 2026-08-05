from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backoffice.pie import PresentationIntelligenceMissionManager


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Run Presentation Intelligence Engine (PIE) on a corporate PPTX and generate dual HTML deliverables."
    )
    p.add_argument("source_pptx", help="Absolute path to source PPTX")
    p.add_argument(
        "--output-root",
        default="reports/pie",
        help="Output root directory where PIE run artifacts will be generated",
    )
    return p


def main() -> None:
    args = build_parser().parse_args()
    manager = PresentationIntelligenceMissionManager()
    result = manager.run(args.source_pptx, args.output_root)
    print(json.dumps(result.__dict__, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
