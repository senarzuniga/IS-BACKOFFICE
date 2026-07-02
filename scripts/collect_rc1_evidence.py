#!/usr/bin/env python3
"""Collect RC1 outputs into releases/rc1_evidence for validation report."""
from __future__ import annotations

import shutil
from pathlib import Path


def find_latest_run(root: Path) -> Path | None:
    out = root / 'ingetrans-reel-simulator' / 'outputs'
    if not out.exists():
        return None
    runs = sorted([p for p in out.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True)
    return runs[0] if runs else None


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    latest = find_latest_run(repo)
    evidence_dir = repo / 'releases' / 'rc1_evidence'
    evidence_dir.mkdir(parents=True, exist_ok=True)

    if not latest:
        print('No run outputs found under ingetrans-reel-simulator/outputs')
        return 2

    print('Collecting outputs from', latest)
    for fname in ['run_summary.json', 'event_log.csv']:
        src = latest / fname
        if src.exists():
            dst = evidence_dir / src.name
            shutil.copy2(src, dst)
            print('Copied', src, '->', dst)
        else:
            print('Missing', src)

    # copy the raw run directory as a zip
    zip_dst = evidence_dir / f'{latest.name}.zip'
    shutil.make_archive(str(zip_dst).replace('.zip',''), 'zip', root_dir=str(latest))
    print('Packed run folder into', zip_dst)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
