from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict


def update_governance_artifacts(iteration_result: Dict) -> Dict[str, str]:
    outputs = {}

    mission_portfolio = Path("reports/spoe/mission_portfolio_spoe.json")
    mission_portfolio.parent.mkdir(parents=True, exist_ok=True)
    mission_payload = {
        "updated_at": datetime.now(UTC).isoformat(),
        "selected_hypothesis": iteration_result.get("hypotheses", {}).get("selected", {}).get("key"),
        "selected_score": iteration_result.get("hypotheses", {}).get("selected", {}).get("global_engineering_score"),
        "opportunities": iteration_result.get("opportunities", []),
    }
    mission_portfolio.write_text(json.dumps(mission_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    outputs["mission_portfolio"] = str(mission_portfolio)

    capability_graph = Path("enterprise_digital_twin/capability_graph_spoe.json")
    capability_payload = {
        "updated_at": datetime.now(UTC).isoformat(),
        "capability_nodes": [
            "Workbench",
            "Template Manager",
            "Engineering Calculator",
            "Document Generator",
            "Knowledge Hub Integration",
            "Coordinator Supervision",
            "Mission Manager",
        ],
        "links": [
            {"from": "Workbench", "to": "Template Manager"},
            {"from": "Template Manager", "to": "Engineering Calculator"},
            {"from": "Engineering Calculator", "to": "Document Generator"},
            {"from": "Document Generator", "to": "Knowledge Hub Integration"},
            {"from": "Knowledge Hub Integration", "to": "Coordinator Supervision"},
            {"from": "Coordinator Supervision", "to": "Mission Manager"},
        ],
    }
    capability_graph.parent.mkdir(parents=True, exist_ok=True)
    capability_graph.write_text(json.dumps(capability_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    outputs["capability_graph"] = str(capability_graph)

    roadmap = Path("reports/spoe/roadmap_spoe.md")
    roadmap.write_text(
        "# SPOE Roadmap\n\n"
        "## Next Engineering Opportunities\n"
        "1. Add pricing configuration matrix per region and customer profile.\n"
        "2. Add PDF and PPT exports on top of DOCX baseline.\n"
        "3. Add multi-template simulation estimators for INGETRANS and AMR.\n"
        "4. Add coordinator evidence bundle and trace log persistence.\n",
        encoding="utf-8",
    )
    outputs["roadmap"] = str(roadmap)

    return outputs
