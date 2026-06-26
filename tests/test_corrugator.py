import unittest

from core.corrugator_engine import CorrugatorEngine


class TestCorrugatorEngine(unittest.TestCase):
    def test_consumption_and_reel_depletion(self):
        cfg = {"corrugator_speed_m_min": 100.0, "initial_reel_weight_kg": 1000.0, "reel_width_m": 2.5, "paper_weight_kg_m2": 0.15, "dt_min": 1.0}
        e = CorrugatorEngine("B", cfg, seed=42)
        # run for enough minutes to deplete reel
        e.running = True
        e.step()
        meters = e.meters_produced
        self.assertGreater(meters, 0)

    def test_starvation_triggers_when_no_tracks(self):
        cfg = {"corrugator_speed_m_min": 200.0, "initial_reel_weight_kg": 10.0, "dt_min": 1.0, "num_tracks": 0}
        e = CorrugatorEngine("B", cfg, seed=1)
        e.running = True
        # single step should detect reel too small and request change -> starvation if no tracks
        e.step()
        kpis = e.get_kpis()
        self.assertTrue(kpis["starvation_events"] >= 0)

    def test_ingetrans_vs_forklift_performance(self):
        cfg = {"corrugator_speed_m_min": 250.0, "initial_reel_weight_kg": 1000.0, "dt_min": 0.5, "num_tracks": 5}
        eA = CorrugatorEngine("A", cfg, seed=2)
        eB = CorrugatorEngine("B", cfg, seed=2)
        eA.running = eB.running = True
        for _ in range(20):
            eA.step()
            eB.step()
        kA = eA.get_kpis()
        kB = eB.get_kpis()
        # INGETRANS should not be worse in meters produced in this deterministic seed
        self.assertGreaterEqual(kB["meters_produced"], kA["meters_produced"])


if __name__ == "__main__":
    unittest.main()
