from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backoffice.spoe import run_ame_iteration, update_governance_artifacts


if __name__ == "__main__":
    result = run_ame_iteration()
    governance = update_governance_artifacts(result)
    print("selected_hypothesis=", result["hypotheses"]["selected"]["key"])
    print("selected_score=", result["hypotheses"]["selected"]["global_engineering_score"])
    print("global_platform_score=", result["platform_score"]["global_platform_score"])
    print("platform_delta=", result["platform_score"]["delta"])
    print("governance_artifacts=", governance)
