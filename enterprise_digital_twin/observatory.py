from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any
from platform_registry.registry import load_registry


def generate_observatory(registry_path: str = "platform_registry/platform_registry.json",
                         capability_registry_path: str = "platform_registry/capability_registry.json",
                         dependency_graph_path: str = "enterprise_digital_twin/dependency_graph.json") -> Dict[str, Any]:
    registry = load_registry(registry_path)
    objects = registry.get("objects", [])
    total = len(objects)

    docs_count = sum(1 for o in objects if "Documentation" in o.get("categories", []) or o.get("path", "").lower().endswith(".md"))
    tests_count = sum(1 for o in objects if o.get("has_tests"))

    doc_coverage = round((docs_count / total * 100) if total else 0, 2)
    test_coverage = round((tests_count / total * 100) if total else 0, 2)

    # capability registry
    cap_count = 0
    obj_caps: Dict[str, list] = {}
    cap_path = Path(capability_registry_path)
    if cap_path.exists():
        try:
            with cap_path.open("r", encoding="utf-8") as f:
                cap_reg = json.load(f)
            cap_count = len(cap_reg.get("capabilities", {}))
            for cap, entry in cap_reg.get("capabilities", {}).items():
                for o in entry.get("objects", []):
                    obj_caps.setdefault(o.get("id"), []).append(cap)
        except Exception:
            cap_count = 0

    # dependency graph for reuse
    dep_path = Path(dependency_graph_path)
    reuse_pct = 0.0
    reuse_objects = 0
    if dep_path.exists():
        try:
            with dep_path.open("r", encoding="utf-8") as f:
                dg = json.load(f)
            edges = dg.get("edges", [])
            inbound = {}
            for e in edges:
                inbound[e.get("to")] = inbound.get(e.get("to"), 0) + 1
            reuse_objects = sum(1 for o in objects if inbound.get(o.get("id"), 0) > 0)
            reuse_pct = round((reuse_objects / total * 100) if total else 0, 2)
        except Exception:
            reuse_pct = 0.0

    # technical debt heuristic: high when doc/test coverage low
    tech_debt = round(max(0.0, 100.0 - (doc_coverage * 0.5 + test_coverage * 0.5)), 2)

    # platform health score (simple weighted average)
    platform_health = round((doc_coverage * 0.3) + (test_coverage * 0.4) + (reuse_pct * 0.3), 2)

    observatory = {
        "total_objects": total,
        "documents": docs_count,
        "doc_coverage_pct": doc_coverage,
        "tests": tests_count,
        "test_coverage_pct": test_coverage,
        "capability_count": cap_count,
        "reuse_objects": reuse_objects,
        "reuse_pct": reuse_pct,
        "technical_debt": tech_debt,
        "platform_health_score": platform_health,
    }

    # save JSON
    out_dir = Path("enterprise_digital_twin")
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "observatory.json").open("w", encoding="utf-8") as f:
        json.dump(observatory, f, indent=2, ensure_ascii=False)

    # write a short markdown report
    rpt = Path("reports") / "observatory_report.md"
    rpt.parent.mkdir(parents=True, exist_ok=True)
    with rpt.open("w", encoding="utf-8") as f:
        f.write("# Platform Observatory Report\n\n")
        f.write(f"Generated: {registry.get('generated_at', '')}\n\n")
        f.write(f"- Total discovered objects: {total}\n")
        f.write(f"- Documentation coverage: {doc_coverage}% ({docs_count})\n")
        f.write(f"- Test coverage: {test_coverage}% ({tests_count})\n")
        f.write(f"- Capabilities discovered: {cap_count}\n")
        f.write(f"- Reuse (objects referenced by others): {reuse_objects} ({reuse_pct}%)\n")
        f.write(f"- Technical debt (est.): {tech_debt}%\n")
        f.write(f"- Platform health score: {platform_health} / 100\n")

    return observatory


if __name__ == '__main__':
    print(generate_observatory())
