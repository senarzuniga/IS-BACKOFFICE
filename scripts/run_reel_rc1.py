#!/usr/bin/env python3
"""RC1 launcher for Reel Load Simulator

Runs the minimal headless runner shipped in `ingetrans-reel-simulator/scripts/run_simulator.py`
and prints the outputs directory for quick demo and acceptance testing.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run RC1 demo of Reel Load Simulator")
    parser.add_argument("--duration", "-d", type=int, default=600, help="Run duration in seconds (default: 600)")
    parser.add_argument("--scenario", "-s", default=None, help="Path to scenario YAML file (optional)")
    parser.add_argument("--tick", "-t", type=float, default=None, help="Tick seconds override (optional)")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed (default: 42)")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    runner = repo_root / "ingetrans-reel-simulator" / "scripts" / "run_simulator.py"
    if not runner.exists():
        print("Error: expected runner not found:", runner)
        return 2

    # default scenario
    if args.scenario:
        scenario_path = Path(args.scenario)
    else:
        scenario_path = repo_root / "ingetrans-reel-simulator" / "06_SCENARIOS" / "scenario_01_baseline_forklift.yaml"

    cmd = [sys.executable, str(runner), "--scenario", str(scenario_path), "--duration", str(args.duration), "--seed", str(args.seed)]
    if args.tick is not None:
        cmd += ["--tick", str(args.tick)]

    print("Running RC1: ", " ".join(cmd))
    try:
        proc = subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print("Simulator failed with exit code", e.returncode)
        return e.returncode
    except Exception as e:
        print("Simulator execution error:", e)
        return 3

    # find latest outputs
    outdir = repo_root / "ingetrans-reel-simulator" / "outputs"
    if outdir.exists():
        runs = sorted([p for p in outdir.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True)
        if runs:
            latest = runs[0]
            print("Run outputs written to:", latest)
            summary = latest / "run_summary.json"
            if summary.exists():
                try:
                    import json

                    with open(summary, "r", encoding="utf-8") as f:
                        js = json.load(f)
                    print("Summary:")
                    print(json.dumps(js, indent=2))
                except Exception:
                    pass
    else:
        print("No outputs directory was created.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
