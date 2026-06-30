#!/usr/bin/env python3
"""Package Reel Load Simulator RC1 into a ZIP for distribution.

This script collects the minimal set of files needed to run RC1 and
produces `releases/reel_simulator_rc1_<timestamp>.zip`.
"""
from __future__ import annotations

import argparse
import shutil
import tempfile
import time
from pathlib import Path


def safe_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dst)


def main() -> int:
    parser = argparse.ArgumentParser(description='Package RC1')
    parser.add_argument('--outdir', '-o', default='releases', help='Output releases directory')
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    tmp = Path(tempfile.mkdtemp(prefix='rc1_pkg_'))
    pkg_root = tmp / 'reel_simulator_rc1'
    pkg_root.mkdir()

    # Files and folders to include
    items = [
        Path('scripts') / 'run_reel_rc1.py',
        Path('run_reel_rc1.bat'),
        Path('README_Reel_load_simulator.md'),
        Path('ingetrans-reel-simulator') / 'scripts' / 'run_simulator.py',
        Path('ingetrans-reel-simulator') / '06_SCENARIOS',
        Path('ingetrans-reel-simulator') / '03_CONFIG_DATABASE',
    ]

    for it in items:
        src = repo_root / it
        if not src.exists():
            print('Warning: skipping missing item', src)
            continue
        rel = it
        dst = pkg_root / rel
        safe_copy(src, dst)

    releases_dir = repo_root / args.outdir
    releases_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime('%Y%m%dT%H%M%SZ')
    base_name = releases_dir / f'reel_simulator_rc1_{ts}'

    archive_path = shutil.make_archive(str(base_name), 'zip', root_dir=str(tmp), base_dir='reel_simulator_rc1')

    print('Created archive:', archive_path)

    # cleanup
    try:
        shutil.rmtree(tmp)
    except Exception:
        pass

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
