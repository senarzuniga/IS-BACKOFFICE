"""Common Workbench Framework for DIGHUB pages.

This module provides reusable primitives for tabbed workbenches:
- state management with namespaced session keys
- simulation job API client
- history loading from output folders
- normalized scoring utilities for architecture decisions
"""

from .models import TabSpec, MetricScore
from .state import get_ns_state, set_ns_value, append_ns_history
from .services import SimulationJobClient, load_run_summaries
from .scoring import normalize_scores, global_score

__all__ = [
    "TabSpec",
    "MetricScore",
    "get_ns_state",
    "set_ns_value",
    "append_ns_history",
    "SimulationJobClient",
    "load_run_summaries",
    "normalize_scores",
    "global_score",
]
