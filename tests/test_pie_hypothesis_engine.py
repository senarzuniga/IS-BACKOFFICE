import unittest

from backoffice.pie.hypothesis_engine import evaluate_hypotheses, resolve_uncertainty
from backoffice.pie.models import Hypothesis


class TestPieHypothesisEngine(unittest.TestCase):
    def test_evaluate_hypotheses_ranks_highest_score_first(self):
        candidates = [
            Hypothesis("A", "low", 5.0, 5.0, 9.0, 6.0, "a"),
            Hypothesis("B", "high", 9.0, 8.8, 8.0, 8.5, "b"),
        ]
        ranked = evaluate_hypotheses(candidates)
        self.assertEqual(ranked[0]["hypothesis"]["key"], "B")

    def test_resolve_uncertainty_uses_fallback_when_empty(self):
        decision = resolve_uncertainty("missing metadata", [])
        self.assertEqual(decision.selected_hypothesis.key, "AUTO-FALLBACK")
        self.assertGreater(decision.score, 0)


if __name__ == "__main__":
    unittest.main()
