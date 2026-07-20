import json
from pathlib import Path


class SimpleStore:
    def __init__(self, path: str = "enterprise_digital_twin/edt.json"):
        self.path = Path(path)

    def save(self, data: dict):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self) -> dict:
        if not self.path.exists():
            return {}
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)
