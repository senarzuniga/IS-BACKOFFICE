#!/usr/bin/env python3
"""Run RC1 and capture console output into releases/rc1_evidence/console_run_output.txt"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--duration', '-d', type=int, default=30)
    parser.add_argument('--scenario', '-s', default='ingetrans-reel-simulator/06_SCENARIOS/scenario_rc1_smoketest.yaml')
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parent.parent
    evidence_dir = repo / 'releases' / 'rc1_evidence'
    evidence_dir.mkdir(parents=True, exist_ok=True)

    runner = repo / 'scripts' / 'run_reel_rc1.py'
    cmd = [sys.executable, str(runner), '--duration', str(args.duration), '--scenario', args.scenario, '--seed', str(args.seed)]

    p = subprocess.run(cmd, capture_output=True, text=True)
    out = p.stdout + '\n' + p.stderr
    log_path = evidence_dir / 'console_run_output.txt'
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(out)

    print('Wrote console output to', log_path)
    return p.returncode


if __name__ == '__main__':
    raise SystemExit(main())
