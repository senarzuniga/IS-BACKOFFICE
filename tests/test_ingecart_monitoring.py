import unittest
from datetime import datetime

from backoffice.analytics.ingecart_monitoring import (
    ROLE_PANELS,
    build_request_alert,
    generate_instant_offer,
    generate_monitoring_snapshot,
    load_monitoring_blueprint,
    suggest_spare_parts,
)


class IngecartMonitoringTests(unittest.TestCase):
    def test_blueprint_contains_requested_sites(self):
        blueprint = load_monitoring_blueprint()
        self.assertEqual(["1", "2", "3", "4", "5"], [site["id"] for site in blueprint["sites"]])
        self.assertTrue(any(site["name"] == "Cascades Sonoco-Calgary" for site in blueprint["sites"]))
        calgary = next(site for site in blueprint["sites"] if site["id"] == "2")
        self.assertEqual(
            [
                "Transfercar + 3 RDC Outfeed Belt Conveyors",
                "2 Belt Conveyors FG + Stitcher Infeed",
            ],
            [equipment["name"] for equipment in calgary["equipment"]],
        )

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

    def test_spare_part_search_returns_technical_matches(self):
        matches = suggest_spare_parts("variador 7.5kw para conveyor con sto", top_k=3)
        self.assertGreater(len(matches), 0)
        top = matches[0]
        self.assertIn("oem_code", top)
        self.assertIn("technical_description", top)
        self.assertGreater(len(top["compatible_alternatives"]), 0)

    def test_request_alert_contains_operational_payload(self):
        alert = build_request_alert(
            request_kind="materials_and_spares",
            requester_name="Ana Ruiz",
            requester_role="Compras",
            plant_id="2",
            plant_name="Cascades Sonoco-Calgary",
            urgency="emergency",
            description="Sensor fotoeléctrico para conveyor de entrada FG",
            suggested_parts=[{"oem_code": "SICK-WTB4-3P2261"}],
        )
        self.assertEqual(alert["alert_type"], "Alerta-Nueva solicitud")
        self.assertEqual(alert["plant_id"], "2")
        self.assertEqual(alert["urgency"], "emergency")
        self.assertIn("SICK-WTB4-3P2261", alert["suggested_oem_codes"])

    def test_calgary_recommendations_match_installed_scope(self):
        snapshot = generate_monitoring_snapshot(
            site_scope="2",
            role="Ingecart",
            now=datetime(2026, 8, 28, 10, 0, 0),
            days=7,
            interval_minutes=60,
        )
        titles = [item["title"] for item in snapshot["recommendations"]]
        self.assertIn("Sincronizar transfercar con entradas de FG y cosedora", titles)
        self.assertTrue(all("BHS" not in title for title in titles))


if __name__ == "__main__":
    unittest.main()
