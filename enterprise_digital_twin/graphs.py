from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Dict, List, Set
from platform_registry.registry import load_registry


def read_file_head(path: Path, limit: int = 65536) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            return f.read(limit)
    except Exception:
        return ""


def build_dependency_and_capability_graphs(registry_path: str = "platform_registry/platform_registry.json", capability_registry_path: str = "platform_registry/capability_registry.json") -> Dict:
    registry = load_registry(registry_path)
    repo_root = Path(registry_path).parent.parent.resolve()
    objects = registry.get("objects", [])

    id_map = {o["id"]: o for o in objects}
    path_map = {o["path"]: o for o in objects}
    # basename map: name without extension -> list of ids
    basename_map: Dict[str, List[str]] = {}
    module_map: Dict[str, str] = {}
    for o in objects:
        p = o.get("path", "")
        stem = Path(p).stem
        basename_map.setdefault(stem, []).append(o["id"])
        if p.endswith(".py"):
            module_name = p[:-3].replace("/", ".")
            module_map[module_name] = o["id"]

    # capability lookup
    obj_caps: Dict[str, List[str]] = {}
    cap_path = Path(capability_registry_path)
    if cap_path.exists():
        try:
            with cap_path.open("r", encoding="utf-8") as f:
                cap_registry = json.load(f)
            for cap_name, entry in cap_registry.get("capabilities", {}).items():
                for obj in entry.get("objects", []):
                    obj_caps.setdefault(obj["id"], []).append(cap_name)
        except Exception:
            pass

    nodes = {}
    edges = []

    for o in objects:
        nodes[o["id"]] = {
            "id": o["id"],
            "name": o.get("name"),
            "path": o.get("path"),
            "categories": o.get("categories", []),
            "capabilities": obj_caps.get(o["id"], []),
        }

    import_from_re = re.compile(r"^\s*from\s+([A-Za-z0-9_\.]+)\s+import", flags=re.M)
    import_re = re.compile(r"^\s*import\s+([A-Za-z0-9_\.]+)", flags=re.M)
    file_ref_re = re.compile(r"[\'\"]([^\'\"]+\.(?:py|md|txt))[\'\"]")

    for o in objects:
        p = o.get("path", "")
        src_id = o["id"]
        if not p.endswith(".py"):
            # still scan for file refs in non-py files
            file_path = repo_root / p
            content = read_file_head(file_path) if file_path.exists() else ""
        else:
            file_path = repo_root / p
            content = read_file_head(file_path) if file_path.exists() else ""

        imports: Set[str] = set()
        for m in import_from_re.finditer(content):
            imports.add(m.group(1))
        for m in import_re.finditer(content):
            imports.add(m.group(1))

        # resolve imports to object ids
        for token in imports:
            # exact module match
            if token in module_map:
                dst = module_map[token]
                edges.append({"from": src_id, "to": dst, "type": "import"})
                continue
            # try last component or basename match
            base = token.split(".")[-1]
            for candidate in basename_map.get(base, []):
                edges.append({"from": src_id, "to": candidate, "type": "import"})
                # do not continue searching other matches for same token
                break

        # find file references like 'other.py' or "doc.md"
        for m in file_ref_re.finditer(content):
            ref = m.group(1).replace("\\", "/")
            # direct path
            if ref in path_map:
                edges.append({"from": src_id, "to": path_map[ref]["id"], "type": "ref"})
                continue
            # basename match
            rstem = Path(ref).stem
            for candidate in basename_map.get(rstem, []):
                edges.append({"from": src_id, "to": candidate, "type": "ref"})
                break

    # capability graph
    cap_edges: Dict[str, Set[str]] = {}
    for e in edges:
        a = e["from"]
        b = e["to"]
        caps_a = obj_caps.get(a, [])
        caps_b = obj_caps.get(b, [])
        for ca in caps_a:
            for cb in caps_b:
                if ca == cb:
                    continue
                cap_edges.setdefault(ca, set()).add(cb)

    capability_graph = {"nodes": [], "edges": []}
    for cap, entry in (cap_edges.items()):
        pass

    # nodes are capability names from cap registry
    try:
        caps = []
        cap_path = Path(capability_registry_path)
        if cap_path.exists():
            with cap_path.open("r", encoding="utf-8") as f:
                cap_registry = json.load(f)
            caps = list(cap_registry.get("capabilities", {}).keys())
        for c in caps:
            capability_graph["nodes"].append({"id": c, "label": c})
        for src_cap, dsts in cap_edges.items():
            for dst_cap in sorted(dsts):
                capability_graph["edges"].append({"from": src_cap, "to": dst_cap})
    except Exception:
        capability_graph = {"nodes": [], "edges": []}

    result = {
        "nodes": nodes,
        "edges": edges,
        "capability_graph": capability_graph,
    }

    # persist
    out_dir = Path("enterprise_digital_twin")
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "dependency_graph.json").open("w", encoding="utf-8") as f:
        json.dump({"nodes": nodes, "edges": edges}, f, indent=2, ensure_ascii=False)
    with (out_dir / "capability_graph.json").open("w", encoding="utf-8") as f:
        json.dump(capability_graph, f, indent=2, ensure_ascii=False)

    return result


if __name__ == "__main__":
    build_dependency_and_capability_graphs()
