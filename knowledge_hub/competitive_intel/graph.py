"""Simple in-memory Knowledge Graph for Competitive Intelligence.

Lightweight representation sufficient for scaffolding and unit tests.
Persist/export functions are JSON-based and optional.
"""

import json
from typing import Dict, List, Optional


class KnowledgeGraph:
    def __init__(self) -> None:
        self.nodes: Dict[str, Dict] = {}
        self.edges: List[Dict] = []

    def add_node(self, node_id: str, type: str = 'Entity', meta: Optional[Dict] = None) -> None:
        self.nodes[node_id] = {'id': node_id, 'type': type, 'meta': meta or {}}

    def add_edge(self, from_id: str, relation: str, to_id: str, weight: float = 1.0, evidence: Optional[int] = None) -> None:
        self.edges.append({'from': from_id, 'relation': relation, 'to': to_id, 'weight': float(weight), 'evidence': evidence})

    def neighbors(self, node_id: str) -> List[str]:
        n = [e['to'] for e in self.edges if e['from'] == node_id]
        n += [e['from'] for e in self.edges if e['to'] == node_id]
        return list(dict.fromkeys(n))

    def export_json(self) -> str:
        return json.dumps({'nodes': list(self.nodes.values()), 'edges': self.edges}, indent=2)
