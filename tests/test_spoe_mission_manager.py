import unittest

from backoffice.spoe.hypothesis_engine import METRICS, Hypothesis, evaluate_hypotheses
from backoffice.spoe.mission_manager import run_ame_iteration


class TestSPOEMissionManager(unittest.TestCase):
    def test_hypothesis_scoring_selects_highest(self):
        h1 = Hypothesis(
            key="A",
            architecture="x",
            implementation_strategy="x",
            expected_engineering_value="x",
            knowledge_gain="x",
            business_value="x",
            reuse="x",
            scalability="x",
            technical_risk="x",
            dependencies=[],
            future_unlock="x",
            metrics_0_10={m: 6.0 for m in METRICS},
        )
        h2 = Hypothesis(
            key="B",
            architecture="x",
            implementation_strategy="x",
            expected_engineering_value="x",
            knowledge_gain="x",
            business_value="x",
            reuse="x",
            scalability="x",
            technical_risk="x",
            dependencies=[],
            future_unlock="x",
            metrics_0_10={m: 8.5 for m in METRICS},
        )
        result = evaluate_hypotheses([h1, h2])
        self.assertEqual(result["selected"]["key"], "B")

    def test_run_ame_iteration_has_required_outputs(self):
        result = run_ame_iteration()
        self.assertIn("platform_state", result)
        self.assertIn("hypotheses", result)
        self.assertIn("platform_score", result)
        self.assertIn("selected", result["hypotheses"])


if __name__ == "__main__":
    unittest.main()
