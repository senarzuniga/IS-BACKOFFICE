"""Capas 2-4: Modelos de datos, memoria corporativa, grafo de conocimiento."""
from __future__ import annotations
import json, hashlib, re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Iterator

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MEMORY_PATH  = PROJECT_ROOT / "data" / "corporate_memory"
GRAPH_PATH   = PROJECT_ROOT / "data" / "knowledge_graph"
for p in [MEMORY_PATH, MEMORY_PATH / "facts", GRAPH_PATH]:
    p.mkdir(parents=True, exist_ok=True)


@dataclass
class Source:
    id: str
    type: str
    path: str
    title: str
    date: str
    page: Optional[int] = None
    checksum: Optional[str] = None


@dataclass
class Fact:
    id: str
    statement: str
    confidence: float
    sources: List[Dict]
    verified_by: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Entity:
    id: str
    name: str
    type: str
    properties: Dict = field(default_factory=dict)
    facts: List[str] = field(default_factory=list)
    relationships: List[Dict] = field(default_factory=list)


class CorporateMemory:
    """Capa 3: Memoria persistente con índice invertido para búsqueda O(1)."""
    def __init__(self) -> None:
        self.path = MEMORY_PATH
        self.facts: Dict[str, Dict] = self._load("facts_index")
        self._inv_index: Dict[str, set] = {}
        self._rebuild_inverted_index()

    def _load(self, name: str) -> Dict:
        p = self.path / f"{name}.json"
        return json.load(open(p, encoding="utf-8")) if p.exists() else {}

    def _save(self, name: str, data: Dict) -> None:
        with open(self.path / f"{name}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _tokenize(self, text: str) -> set:
        return {w.lower() for w in re.findall(r"\w{4,}", text)}

    def _rebuild_inverted_index(self) -> None:
        self._inv_index = {}
        for fid, meta in self.facts.items():
            for tok in self._tokenize(meta.get("statement", "")):
                self._inv_index.setdefault(tok, set()).add(fid)

    def save_fact(self, fact: Fact) -> str:
        fid = fact.id or hashlib.md5(fact.statement.encode()).hexdigest()[:16]
        fact_path = self.path / "facts" / f"{fid}.json"
        data = asdict(fact); data["id"] = fid
        with open(fact_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        self.facts[fid] = {
            "statement": fact.statement[:160],
            "confidence": fact.confidence,
            "created_at": fact.created_at,
        }
        self._save("facts_index", self.facts)
        for tok in self._tokenize(fact.statement):
            self._inv_index.setdefault(tok, set()).add(fid)
        return fid

    def find_related(self, query: str, min_confidence: float = 0.5, limit: int = 50) -> List[Dict]:
        tokens = self._tokenize(query)
        if not tokens: return []
        candidate_ids = set.intersection(*[self._inv_index.get(t, set()) for t in tokens]) \
                        if len(tokens) > 1 else self._inv_index.get(tokens.pop(), set())
        results = []
        for fid in candidate_ids:
            meta = self.facts.get(fid)
            if not meta or meta["confidence"] < min_confidence: continue
            fp = self.path / "facts" / f"{fid}.json"
            if fp.exists():
                with open(fp, "r", encoding="utf-8") as f:
                    results.append(json.load(f))
            if len(results) >= limit: break
        return results

    def stats(self) -> Dict:
        if not self.facts: return {"total_facts": 0, "avg_confidence": 0.0, "unique_tokens": 0}
        return {
            "total_facts": len(self.facts),
            "avg_confidence": round(sum(f["confidence"] for f in self.facts.values()) / len(self.facts), 3),
            "unique_tokens": len(self._inv_index),
        }


class KnowledgeGraph:
    """Capa 4: Grafo de entidades con serialización incremental."""
    def __init__(self) -> None:
        self.path = GRAPH_PATH
        self.entities: Dict[str, Entity] = {}
        self._dirty = False
        self._load()

    def _load(self) -> None:
        p = self.path / "graph.json"
        if p.exists():
            data = json.load(open(p, encoding="utf-8"))
            for eid, ed in data.get("entities", {}).items():
                self.entities[eid] = Entity(**ed)

    def _save(self) -> None:
        if not self._dirty: return
        data = {"entities": {eid: asdict(e) for eid, e in self.entities.items()},
                "updated_at": datetime.utcnow().isoformat()}
        with open(self.path / "graph.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        self._dirty = False

    def upsert_entity(self, name: str, etype: str, properties: Dict = None) -> str:
        eid = hashlib.md5(f"{etype}:{name.lower()}".encode()).hexdigest()[:16]
        if eid in self.entities:
            if properties: self.entities[eid].properties.update(properties)
        else:
            self.entities[eid] = Entity(id=eid, name=name, type=etype, properties=properties or {})
        self._dirty = True; self._save(); return eid

    def link(self, from_id: str, to_id: str, rel_type: str, properties: Dict = None) -> None:
        if from_id not in self.entities or to_id not in self.entities: return
        rel = {"target": to_id, "type": rel_type, "properties": properties or {}}
        if rel not in self.entities[from_id].relationships:
            self.entities[from_id].relationships.append(rel)
            self._dirty = True; self._save()

    def find(self, name: str) -> Optional[Entity]:
        for e in self.entities.values():
            if e.name.lower() == name.lower(): return e
        return None

    def stats(self) -> Dict:
        types: Dict[str, int] = {}
        for e in self.entities.values():
            types[e.type] = types.get(e.type, 0) + 1
        return {"total_entities": len(self.entities), "by_type": types,
                "total_relationships": sum(len(e.relationships) for e in self.entities.values())}
