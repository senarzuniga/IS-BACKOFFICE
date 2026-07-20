from __future__ import annotations

import json
from typing import List, Dict
from pathlib import Path
from platform_registry.registry import load_registry
from enterprise_digital_twin.model import EDTObject


def build_edt_from_discovery(registry_path: str = "platform_registry/platform_registry.json") -> Dict:
    registry = load_registry(registry_path)
    objects = registry.get("objects", [])
    edt = {"generated_at": registry.get("generated_at"), "objects": []}
    for o in objects:
        obj = EDTObject(
            id=o.get("id"),
            type=','.join(o.get("categories", [])) or "Unknown",
            name=o.get("name"),
            description=o.get("description"),
        )
        edt["objects"].append(obj.to_dict())

    return edt


def save_edt(edt: Dict, path: str = "enterprise_digital_twin/edt.json"):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(edt, f, indent=2, ensure_ascii=False)
