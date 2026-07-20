import json
from pathlib import Path
from typing import List, Dict


class PlatformRegistryClient:
    def __init__(self, registry_path: str = "platform_registry/platform_registry.json", capability_path: str = "platform_registry/capability_registry.json"):
        self.registry_path = Path(registry_path)
        self.capability_path = Path(capability_path)
        self._registry = None
        self._capability_registry = None

    def load_registry(self) -> Dict:
        if self._registry is None:
            with self.registry_path.open("r", encoding="utf-8") as f:
                self._registry = json.load(f)
        return self._registry

    def load_capability_registry(self) -> Dict:
        if self._capability_registry is None:
            with self.capability_path.open("r", encoding="utf-8") as f:
                self._capability_registry = json.load(f)
        return self._capability_registry

    def list_capabilities(self) -> List[str]:
        cap = self.load_capability_registry().get("capabilities", {})
        return sorted(cap.keys(), key=lambda k: -cap[k]["count"]) if cap else []

    def find_objects_by_capability(self, capability: str, limit: int = 100) -> List[Dict]:
        cap = self.load_capability_registry().get("capabilities", {})
        entry = cap.get(capability, {})
        return entry.get("objects", [])[:limit]

    def resolve_capability_from_intent(self, intent: str, top_k: int = 5) -> List[Dict]:
        """Naive intent->capability resolver: rank capabilities by token overlap."""
        caps = self.load_capability_registry().get("capabilities", {})
        if not caps:
            return []
        intent_l = intent.lower()
        scores = []
        for cap_name, data in caps.items():
            score = 0
            # simple heuristics: token overlap
            for token in intent_l.split():
                if token in cap_name.lower():
                    score += 2
            # small boost for exact match
            if intent_l.strip() == cap_name.lower():
                score += 10
            if score > 0:
                scores.append((cap_name, score, data.get("count", 0)))
        scores.sort(key=lambda x: (-x[1], -x[2]))
        return [{"capability": s[0], "score": s[1], "count": s[2]} for s in scores[:top_k]]

