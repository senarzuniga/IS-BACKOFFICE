#!/usr/bin/env python3
"""Watcher: keeps the Enterprise Digital Twin updated by reusing the discovery output.

This initial watcher is simple: it re-runs ingest (which relies on the discovery output)
and rebuilds the EDT. In later iterations it should watch file-system events.
"""
from __future__ import annotations

import time
from pathlib import Path
from enterprise_digital_twin.builder import build_edt_from_discovery, save_edt
from platform_registry.registry import load_registry


def run_once():
    # Build EDT from current platform_registry
    edt = build_edt_from_discovery()
    save_edt(edt)
    print("EDT built: enterprise_digital_twin/edt.json")


def run_loop(interval: int = 60):
    print("Starting watcher loop. Press Ctrl+C to stop.")
    try:
        while True:
            run_once()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Watcher stopped.")


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--interval', type=int, default=60, help='Polling interval in seconds')
    args = p.parse_args()
    run_loop(args.interval)
