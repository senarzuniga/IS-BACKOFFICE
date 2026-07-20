from __future__ import annotations

import json
from pathlib import Path
from platform_registry.client import PlatformRegistryClient


def generate_navigation(output_path: str = "enterprise_digital_twin/navigation.json"):
    client = PlatformRegistryClient()
    caps = client.list_capabilities()
    nav = {"generated_at": None, "menu": []}
    # simple menu: capabilities -> first 10 implementations
    for c in caps:
        objs = client.find_objects_by_capability(c, limit=10)
        nav["menu"].append({"capability": c, "items": [{"name": o['name'], "path": o['path']} for o in objs]})

    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(nav, f, indent=2, ensure_ascii=False)
    print(f"Navigation written to: {p}")
    return nav


if __name__ == '__main__':
    generate_navigation()
