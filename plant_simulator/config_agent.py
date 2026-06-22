from types import SimpleNamespace
from typing import Any, Dict, List, Tuple


class ConfigAgent:
    """Lightweight ConfigAgent stub for tests and demo.

    Methods:
      - build_config(answers) -> config object with attributes used by the app
      - demo_scenarios() -> list of (label, answers_dict)
    """

    def build_config(self, answers: Dict[str, Any]):
        name = answers.get("name") or answers.get("plant_name") or "Demo Plant"
        plant_type = SimpleNamespace(value=answers.get("plant_type", "DemoType"))
        converters = [SimpleNamespace(id=1, name="Converter1")]
        cfg = SimpleNamespace(name=name, plant_type=plant_type, converters=converters)
        return cfg

    def demo_scenarios(self) -> List[Tuple[str, Dict[str, Any]]]:
        return [
            ("Default demo", {"answers": {"plant_type": "DemoType", "capacity": 1000}}),
            ("High throughput", {"answers": {"plant_type": "HighSpeed", "capacity": 5000}}),
        ]
