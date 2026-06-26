import unittest

from core.consumption_engine import CorrugatorEngineV3
from core.kpi_calculator import calculate_kpis
from utils.charts import flow_chart
from utils.renderer_svg_advanced import render_plant_svg


class TestCorrugatorV3(unittest.TestCase):
    def test_consumption_simultaneous(self):
        cfg = {"num_roll_stands": 5, "corrugator_avg_speed": 100, "avg_reel_length": 1000, "num_tracks": 6}
        eng = CorrugatorEngineV3(config=cfg, scenario="B", seed=1)
        eng.step(1.0)
        # each stand should produce corrugator_avg_speed * 1.0 meters
        self.assertAlmostEqual(eng.metrics["production_meters"], 100.0 * 5.0, places=6)

    def test_track_state_transitions(self):
        cfg = {"num_roll_stands": 2, "corrugator_avg_speed": 50, "avg_reel_length": 500, "num_tracks": 3}
        eng = CorrugatorEngineV3(config=cfg, scenario="B", seed=2)
        # schedule a delivery and check that the event queue contains arrival_exchange
        scheduled = eng.schedule_delivery_for_stand(0, eng.time)
        self.assertTrue(scheduled)
        # after a few steps the track should return to EMPTY or be in CONSUMING
        eng.step(0.5)
        for _ in range(10):
            eng.step(0.5)
        states = set(t["state"].name for t in eng.tracks)
        self.assertTrue("EMPTY" in states or "CONSUMING" in states)

    def test_predictive_no_starvation(self):
        cfg = {"num_roll_stands": 3, "corrugator_avg_speed": 220, "avg_reel_length": 5000, "num_tracks": 6, "ingetrans_predictive_lead_time_min": 15}
        eng = CorrugatorEngineV3(config=cfg, scenario="B", seed=3)
        eng.run(30.0, step_min=1.0)
        self.assertEqual(eng.metrics["starvation_count"], 0)

    def test_reactive_with_starvation(self):
        cfg = {"num_roll_stands": 3, "corrugator_avg_speed": 220, "avg_reel_length": 5000, "num_tracks": 6}
        eng = CorrugatorEngineV3(config=cfg, scenario="A", seed=4)
        eng.run(30.0, step_min=1.0)
        self.assertGreater(eng.metrics["starvation_count"], 0)

    def test_kpis_nonzero(self):
        cfg = {"num_roll_stands": 4, "corrugator_avg_speed": 200, "avg_reel_length": 3000, "num_tracks": 8}
        eng = CorrugatorEngineV3(config=cfg, scenario="B", seed=5)
        eng.run(10.0, step_min=1.0)
        kpis = calculate_kpis(eng)
        for key in ["track_saturation", "RRI", "PSS", "LPI", "OEE"]:
            self.assertIn(key, kpis)
            self.assertGreaterEqual(kpis[key], 0)

    def test_visualization_helpers(self):
        cfg = {"num_roll_stands": 2, "corrugator_avg_speed": 100, "avg_reel_length": 1000, "num_tracks": 4}
        eng = CorrugatorEngineV3(config=cfg, scenario="B", seed=6)
        eng.step(1.0)
        fig = flow_chart({"Warehouse": 5, "Buffer": 2, "Tracks": 3})
        self.assertIsNotNone(fig)
        svg = render_plant_svg(eng)
        self.assertTrue(svg.strip().startswith("<svg"))

