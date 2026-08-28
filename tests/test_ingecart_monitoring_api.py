"""Tests for the Ingecart Monitoring FastAPI route handlers and analytics __init__ exports."""
import unittest

from backoffice.analytics import (
    generate_instant_offer,
    generate_monitoring_snapshot,
    get_scope_label,
    get_scope_options,
    load_monitoring_blueprint,
    ROLE_PANELS,
    FORMULA_LIBRARY,
)


class TestIngecartAnalyticsInitExports(unittest.TestCase):
    """Verify that backoffice.analytics.__init__ re-exports the monitoring symbols."""

    def test_blueprint_accessible_via_package(self):
        bp = load_monitoring_blueprint()
        self.assertEqual(len(bp["sites"]), 5)

    def test_role_panels_accessible_via_package(self):
        self.assertIn("Ingecart", ROLE_PANELS)
        self.assertIn("Operario", ROLE_PANELS)

    def test_formula_library_accessible_via_package(self):
        self.assertGreater(len(FORMULA_LIBRARY), 0)
        self.assertTrue(any(f["metric"] == "OEE" for f in FORMULA_LIBRARY))

    def test_scope_options(self):
        options = get_scope_options()
        self.assertEqual(options[0], "all")
        self.assertIn("1", options)
        self.assertIn("5", options)

    def test_scope_label_all(self):
        bp = load_monitoring_blueprint()
        label = get_scope_label("all", bp)
        self.assertIn("Todas", label)

    def test_scope_label_site(self):
        bp = load_monitoring_blueprint()
        label = get_scope_label("2", bp)
        self.assertIn("Calgary", label)


class TestIngecartMonitoringAPIRoute(unittest.TestCase):
    """Test the FastAPI route handler functions directly (no HTTP layer)."""

    def setUp(self):
        from api.routes.ingecart_monitoring import (
            get_blueprint,
            get_formulas,
            get_roles,
            get_scopes,
            post_snapshot,
            post_offer,
            SnapshotRequest,
            OfferRequest,
        )
        self.get_blueprint = get_blueprint
        self.get_formulas = get_formulas
        self.get_roles = get_roles
        self.get_scopes = get_scopes
        self.post_snapshot = post_snapshot
        self.post_offer = post_offer
        self.SnapshotRequest = SnapshotRequest
        self.OfferRequest = OfferRequest

    def test_get_blueprint_structure(self):
        result = self.get_blueprint()
        self.assertEqual(result["company_code"], "ingecart-monitoring")
        self.assertEqual(result["site_count"], 5)
        for site in result["sites"]:
            self.assertIn("equipment", site)
            self.assertGreater(site["equipment_count"], 0)

    def test_get_roles_returns_all_roles(self):
        result = self.get_roles()
        self.assertIn("Ingecart", result)
        self.assertIn("Operario", result)
        self.assertIn("Gerencia", result)
        for role_data in result.values():
            self.assertIn("focus_metrics", role_data)
            self.assertIn("documents", role_data)

    def test_get_formulas_returns_oee(self):
        result = self.get_formulas()
        metrics = [f["metric"] for f in result]
        self.assertIn("OEE", metrics)
        self.assertIn("LPI", metrics)

    def test_get_scopes_structure(self):
        result = self.get_scopes()
        self.assertIn("scopes", result)
        values = [s["value"] for s in result["scopes"]]
        self.assertIn("all", values)
        self.assertIn("1", values)
        self.assertIn("5", values)

    def test_post_snapshot_returns_portfolio(self):
        req = self.SnapshotRequest(site_scope="1", role="Jefe de planta", days=3, interval_minutes=60)
        result = self.post_snapshot(req)
        self.assertIn("portfolio", result)
        self.assertIn("oee_pct", result["portfolio"])
        self.assertIn("alerts", result)
        self.assertIn("recommendations", result)
        self.assertGreater(result["series_count"], 0)

    def test_post_snapshot_all_scope(self):
        req = self.SnapshotRequest(site_scope="all", role="Ingecart", days=2, interval_minutes=60)
        result = self.post_snapshot(req)
        self.assertEqual(len(result["site_summaries"]), 5)

    def test_post_offer_contract(self):
        req = self.OfferRequest(
            site_scope="2",
            offer_kind="maintenance_contract",
            target_equipment_id="all",
            coverage="24x7",
            urgency="priority",
        )
        result = self.post_offer(req)
        self.assertTrue(result["reference"].startswith("ING-MON-"))
        self.assertGreater(len(result["lines"]), 0)
        self.assertGreater(result["monthly_total_eur"], 0)

    def test_post_offer_materials(self):
        req = self.OfferRequest(
            site_scope="all",
            offer_kind="materials_and_spares",
            target_equipment_id="all",
            coverage="business_hours",
            urgency="standard",
        )
        result = self.post_offer(req)
        self.assertGreater(result["capex_total_eur"], 0)

    def test_post_snapshot_invalid_scope_raises(self):
        from fastapi import HTTPException
        req = self.SnapshotRequest(site_scope="99", role="Ingecart", days=2, interval_minutes=60)
        with self.assertRaises(HTTPException):
            self.post_snapshot(req)

    def test_post_snapshot_invalid_role_raises(self):
        from fastapi import HTTPException
        req = self.SnapshotRequest(site_scope="all", role="Desconocido", days=2, interval_minutes=60)
        with self.assertRaises(HTTPException):
            self.post_snapshot(req)

    def test_post_offer_invalid_kind_raises(self):
        from fastapi import HTTPException
        req = self.OfferRequest(site_scope="all", offer_kind="fake_kind")
        with self.assertRaises(HTTPException):
            self.post_offer(req)


if __name__ == "__main__":
    unittest.main()
