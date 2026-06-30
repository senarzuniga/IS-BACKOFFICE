#!/usr/bin/env python3
"""Sanity check for Reel Load Simulator RC1.

Performs lightweight validations (files, deps) and an optional short
headless run to ensure the RC1 runner produces outputs.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def check_pyyaml() -> tuple[bool, str]:
    try:
        import yaml  # type: ignore
        return True, ""
    except Exception as e:
        return False, str(e)


def run_headless(duration: int, seed: int, tick: float | None) -> tuple[int, str]:
    cmd = [sys.executable, str(Path('scripts') / 'run_reel_rc1.py'), '--duration', str(duration), '--seed', str(seed)]
    if tick is not None:
        cmd += ['--tick', str(tick)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = proc.stdout + proc.stderr
    return proc.returncode, out


def find_latest_output() -> Path | None:
    outdir = Path('ingetrans-reel-simulator') / 'outputs'
    if not outdir.exists():
        return None
    runs = sorted([p for p in outdir.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True)
    return runs[0] if runs else None


def main() -> int:
    parser = argparse.ArgumentParser(description='Sanity check RC1')
    parser.add_argument('--no-run', action='store_true', help='Do not execute the simulator run (only checks files/deps)')
    parser.add_argument('--duration', '-d', type=int, default=2, help='Duration in seconds for a short sanity run')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--tick', type=float, default=None)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    runner = repo_root / 'ingetrans-reel-simulator' / 'scripts' / 'run_simulator.py'
    if not runner.exists():
        print('ERROR: runner not found at', runner)
        return 2

    scenarios = repo_root / 'ingetrans-reel-simulator' / '06_SCENARIOS'
    if not scenarios.exists() or not any(scenarios.glob('*.yaml')):
        print('ERROR: no scenarios found in', scenarios)
        return 2

    ok, msg = check_pyyaml()
    if not ok:
        print('ERROR: PyYAML not available:', msg)
        print('Install with: pip install pyyaml')
        return 3

    print('Basic checks: runner and scenarios found, PyYAML available')

    if args.no_run:
        print('Skipping simulator execution (--no-run).')
        return 0

    print(f'Executing a short headless run ({args.duration}s) to verify outputs...')
    rc, out = run_headless(args.duration, args.seed, args.tick)
    print(out)
    if rc != 0:
        print('Simulator process returned code', rc)
        return rc

    latest = find_latest_output()
    if not latest:
        print('ERROR: No outputs created under ingetrans-reel-simulator/outputs')
        return 4

    print('Outputs created at:', latest)
    summary = latest / 'run_summary.json'
    if summary.exists():
        try:
            with open(summary, 'r', encoding='utf-8') as f:
                js = json.load(f)
            print('Run summary:')
            print(json.dumps(js, indent=2))
        except Exception:
            print('Could not read run_summary.json')
    else:
        print('Warning: run_summary.json not found in', latest)

    print('Sanity check: PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
