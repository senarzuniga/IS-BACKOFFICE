from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List


@dataclass(frozen=True)
class TabSpec:
    key: str
    title: str
    renderer: Callable[[], None]


@dataclass(frozen=True)
class MetricScore:
    name: str
    value: float


def metrics_to_dict(metrics: List[MetricScore]) -> Dict[str, float]:
    return {m.name: float(m.value) for m in metrics}
