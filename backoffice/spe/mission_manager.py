from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backoffice.his.studio import HtmlIntelligenceStudio

from .database import SPEDatabase
from .generator import ProposalHTMLGenerator
from .models import MissionEntry, Proposal, ProposalVersion


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SPE_REPORT_DIR = REPO_ROOT / "reports" / "spe"
MISSION_REGISTRY = SPE_REPORT_DIR / "mission_registry.jsonl"
KNOWLEDGE_HUB_LOG = REPO_ROOT / "knowledge_hub" / "spe" / "mission_knowledge.jsonl"
ENTERPRISE_MEMORY = REPO_ROOT / "enterprise_digital_twin" / "spe_memory.json"
TRUTH_GRAPH = REPO_ROOT / "enterprise_digital_twin" / "truth_graph_spe.json"


class SPEMissionManager:
    """Mission-driven orchestration for Service Proposal Engine operations."""

    def __init__(self, db: SPEDatabase | None = None, generator: ProposalHTMLGenerator | None = None) -> None:
        self.db = db or SPEDatabase()
        self.generator = generator or ProposalHTMLGenerator()
        self.his = HtmlIntelligenceStudio(corporate_model_path=self.generator.corporate_model_path)

    def run_mission(self, proposal: Proposal, action: str, objective: str, payload: dict[str, Any] | None = None) -> MissionEntry:
        mission_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S") + "_" + action
        mission = MissionEntry(
            mission_id=mission_id,
            name=action,
            status="completed",
            agents=["Mission Manager", "AI Coordinator", "Assistant"],
            prompts=[objective],
            decisions=["AHDE-selected deterministic path"],
            evidence=[],
            kpis={},
            created_at=datetime.now(UTC).isoformat(),
            completed_at=datetime.now(UTC).isoformat(),
        )
        proposal.missions.append(mission)
        self._register(action=action, objective=objective, proposal=proposal, payload=payload or {}, mission_id=mission_id)
        return mission

    def save_version(self, proposal: Proposal, author: str, reason: str) -> Proposal:
        html = self.generator.generate(proposal, preview=False)
        version_num = len(proposal.versions) + 1
        proposal.version = max(proposal.version + 1, version_num)
        proposal.html_output = html
        proposal.versions.append(
            ProposalVersion(
                version=version_num,
                created_at=datetime.now(UTC).isoformat(),
                author=author,
                changes=reason,
                html_snapshot=html[:8000],
            )
        )
        self.run_mission(proposal, "save_and_version", reason, {"version": version_num})
        self.db.update(proposal, change=reason)
        return proposal

    def duplicate(self, proposal_id: str, new_customer: str | None = None) -> Proposal | None:
        dup = self.db.duplicate(proposal_id, new_customer=new_customer)
        if dup is None:
            return None
        self.run_mission(dup, "duplicate", "Duplicate proposal with automatic collision-free number")
        self.db.update(dup, change="Duplicated proposal")
        return dup

    def publish(self, proposal: Proposal, author: str = "Mission Manager") -> dict[str, Any]:
        if not proposal.report_id:
            self.generator.generate(proposal, preview=False)
        model_path = self.generator.get_model_path(proposal)
        if not model_path:
            raise RuntimeError("Missing HIS model path for proposal publication")
        publish_result = self.his.publish_document(model_path, author=author)
        proposal.status = "accepted"
        self.run_mission(
            proposal,
            "publish",
            "Publish proposal after validator gates",
            {"publication_state": publish_result.get("publication_state", "")},
        )
        self.db.update(proposal, change="Published proposal")
        return publish_result

    def export_release_bundle(self, proposal: Proposal) -> str:
        model_path = self.generator.get_model_path(proposal)
        if not model_path:
            raise RuntimeError("Missing HIS model path for export")
        zip_path = self.his.export_release_bundle(model_path)
        self.run_mission(proposal, "export_bundle", "Export release bundle", {"zip_path": zip_path})
        self.db.update(proposal, change="Exported release bundle")
        return zip_path

    def _register(self, *, action: str, objective: str, proposal: Proposal, payload: dict[str, Any], mission_id: str) -> None:
        row = {
            "ts": datetime.now(UTC).isoformat(),
            "mission_id": mission_id,
            "action": action,
            "objective": objective,
            "proposal_id": proposal.id,
            "proposal_number": proposal.number,
            "payload": payload,
        }
        MISSION_REGISTRY.parent.mkdir(parents=True, exist_ok=True)
        with MISSION_REGISTRY.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        KNOWLEDGE_HUB_LOG.parent.mkdir(parents=True, exist_ok=True)
        with KNOWLEDGE_HUB_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        self._update_enterprise_memory(row)
        self._update_truth_graph(row)

    def _update_enterprise_memory(self, row: dict[str, Any]) -> None:
        ENTERPRISE_MEMORY.parent.mkdir(parents=True, exist_ok=True)
        items = []
        if ENTERPRISE_MEMORY.exists():
            try:
                items = json.loads(ENTERPRISE_MEMORY.read_text(encoding="utf-8"))
                if not isinstance(items, list):
                    items = []
            except Exception:
                items = []
        items.append(row)
        ENTERPRISE_MEMORY.write_text(json.dumps(items[-200:], indent=2, ensure_ascii=False), encoding="utf-8")

    def _update_truth_graph(self, row: dict[str, Any]) -> None:
        TRUTH_GRAPH.parent.mkdir(parents=True, exist_ok=True)
        graph = {"nodes": [], "edges": []}
        if TRUTH_GRAPH.exists():
            try:
                graph = json.loads(TRUTH_GRAPH.read_text(encoding="utf-8"))
            except Exception:
                graph = {"nodes": [], "edges": []}
        nodes = graph.setdefault("nodes", [])
        edges = graph.setdefault("edges", [])
        proposal_node = f"proposal:{row['proposal_number']}"
        mission_node = f"mission:{row['mission_id']}"
        if proposal_node not in nodes:
            nodes.append(proposal_node)
        if mission_node not in nodes:
            nodes.append(mission_node)
        edges.append({"from": mission_node, "to": proposal_node, "relation": row["action"], "ts": row["ts"]})
        TRUTH_GRAPH.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
