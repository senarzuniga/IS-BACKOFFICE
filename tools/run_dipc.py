from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backoffice.dipc import DocumentIntelligencePublishingCenter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Document Intelligence & Publishing Center missions.")
    parser.add_argument("source", help="Source PPTX path or existing document_model.json path")
    parser.add_argument("--output-root", default="reports/dipc", help="Output root for DIPC artifacts")
    parser.add_argument("--command", help="Optional command mission to apply to an existing document model")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    center = DocumentIntelligencePublishingCenter()
    source = Path(args.source)
    if args.command:
        result = center.apply_mission(str(source), args.command, args.output_root)
    else:
        result = center.build_from_powerpoint(str(source), args.output_root)
    print(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
