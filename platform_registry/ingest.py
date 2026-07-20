#!/usr/bin/env python3
"""Ingest discovery registry and produce capability registry and reports."""
from __future__ import annotations

import sys
from pathlib import Path
from platform_registry.registry import load_registry, build_capability_registry, save_capability_registry


def main():
    root = Path('.')
    reg_path = root / 'platform_registry' / 'platform_registry.json'
    if not reg_path.exists():
        print('Discovery registry not found. Run tools/discovery/discover_platform.py first.')
        sys.exit(1)

    registry = load_registry(str(reg_path))
    cap_registry = build_capability_registry(registry)
    save_capability_registry(cap_registry, path=str(root / 'platform_registry' / 'capability_registry.json'))

    # simple markdown inventory
    report = root / 'reports' / 'capability_inventory.md'
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open('w', encoding='utf-8') as f:
        f.write('# Capability Inventory\n\n')
        f.write(f"Generated from: {reg_path}\n\n")
        for cap, data in sorted(cap_registry.get('capabilities', {}).items(), key=lambda x: -x[1]['count']):
            f.write(f"## {cap} ({data['count']})\n\n")
            for obj in data['objects'][:100]:
                f.write(f"- {obj['name']} — `{obj['path']}`\n")
            f.write('\n')

    print('Capability registry generated at platform_registry/capability_registry.json')
    print('Capability inventory written to reports/capability_inventory.md')


if __name__ == '__main__':
    main()
