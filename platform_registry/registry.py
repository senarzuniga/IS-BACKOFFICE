import json
from pathlib import Path
from typing import Dict, List


def load_registry(path: str = "platform_registry/platform_registry.json") -> Dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Registry file not found: {path}")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_capability_registry(registry: Dict) -> Dict:
    """Map discovered objects to capabilities using simple heuristics."""
    cap_map = {}
    objects = registry.get("objects", [])
    for o in objects:
        cats = o.get("categories", [])
        name = o.get("name", "")
        desc = o.get("description", "") or ""
        detected_caps = set()
        for c in cats:
            # normalize category -> capability
            if c in ("Workbench", "UI Component"):
                detected_caps.add("Workbench")
            elif c == "Agent":
                detected_caps.add("Agent")
            elif c == "Simulation":
                detected_caps.add("Simulation")
            elif c == "Engine":
                detected_caps.add("Engine")
            elif c == "Knowledge Source":
                detected_caps.add("Knowledge")
            elif c == "API Service":
                detected_caps.add("API")
            elif c == "Documentation":
                detected_caps.add("Documentation")
            elif c == "Module":
                detected_caps.add("Module")
            else:
                detected_caps.add(c)

        # keyword-based enrichment
        t = (name + " " + desc).lower()
        if any(k in t for k in ("layout", "factory", "plant", "layout")):
            detected_caps.add("Factory Layout Analysis")
        if any(k in t for k in ("flow", "material flow", "throughput")):
            detected_caps.add("Material Flow Optimization")
        if "amr" in t or "robot" in t or "fleet" in t:
            detected_caps.add("AMR Fleet Optimization")
        if "simulation" in t or "simulator" in t:
            detected_caps.add("Simulation")
        if "document" in t or name.endswith(('.md', '.txt', '.pdf')):
            detected_caps.add("Document Intelligence")

        for cap in detected_caps:
            cap_map.setdefault(cap, []).append({
                "id": o.get("id"),
                "name": o.get("name"),
                "path": o.get("path"),
            })

    capability_registry = {"generated_at": registry.get("generated_at"), "capabilities": {}}
    for k, v in cap_map.items():
        capability_registry["capabilities"][k] = {"count": len(v), "objects": v}
    return capability_registry


def save_capability_registry(cap_registry: Dict, path: str = "platform_registry/capability_registry.json"):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(cap_registry, f, indent=2, ensure_ascii=False)
