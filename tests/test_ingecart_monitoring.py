import unittest
from datetime import datetime

from backoffice.analytics.ingecart_monitoring import (
    ROLE_PANELS,
    generate_instant_offer,
    generate_monitoring_snapshot,
    load_monitoring_blueprint,
)


class IngecartMonitoringTests(unittest.TestCase):
    def test_blueprint_contains_requested_sites(self):
        blueprint = load_monitoring_blueprint()
        self.assertEqual(["1", "2", "3", "4", "5"], [site["id"] for site in blueprint["sites"]])
        self.assertTrue(any(site["name"] == "Cascades Sonoco-Calgary" for site in blueprint["sites"]))

    def test_snapshot_respects_scope_and_role(self):
        snapshot = generate_monitoring_snapshot(
            site_scope="4",
            role="Mantenimiento",
            now=datetime(2026, 8, 28, 10, 0, 0),
            days=7,
            interval_minutes=60,
        )
        self.assertEqual("Mantenimiento", snapshot["role"])
        self.assertEqual(ROLE_PANELS["Mantenimiento"]["description"], snapshot["role_panel"]["description"])
        self.assertTrue(all(row["site_id"] == "4" for row in snapshot["equipment_latest"]))
        self.assertGreater(len(snapshot["series"]), 0)

    def test_holiday_rows_have_no_throughput(self):
        snapshot = generate_monitoring_snapshot(
            site_scope="5",
            role="Ingecart",
            now=datetime(2026, 8, 28, 10, 0, 0),
            days=7,
            interval_minutes=60,
        )
        holiday_rows = [row for row in snapshot["series"] if row["holiday"] and row["state"] == "holiday"]
        self.assertGreater(len(holiday_rows), 0)
        self.assertTrue(all(float(row["throughput_per_hour"]) == 0.0 for row in holiday_rows))

    def test_offer_generation_returns_reference_and_lines(self):
        snapshot = generate_monitoring_snapshot(
            site_scope="all",
            role="Ingecart",
            now=datetime(2026, 8, 28, 10, 0, 0),
            days=3,
            interval_minutes=60,
        )
        offer = generate_instant_offer(snapshot, "materials_and_spares", "all", "24x7", "priority")
        self.assertTrue(offer["reference"].startswith("ING-MON-"))
        self.assertGreater(len(offer["lines"]), 0)


if __name__ == "__main__":
    unittest.main()
