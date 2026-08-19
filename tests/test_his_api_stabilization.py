from __future__ import annotations

import unittest

from backoffice.his import HtmlIntelligenceStudio


class TestHISApiStabilization(unittest.TestCase):
    def setUp(self) -> None:
        self.studio = HtmlIntelligenceStudio()

    def test_mandatory_public_api_methods_exist(self) -> None:
        mandatory = [
            "list_documents",
            "get_document",
            "create_document",
            "delete_document",
            "duplicate_document",
            "save_document",
            "open_document",
            "generate_html",
            "preview_document",
            "publish_document",
            "list_versions",
            "restore_version",
            "search",
            "statistics",
            "quality_report",
            "get_repository_catalog",
            "resolve_asset_candidates",
            "theme_profiles",
            "run_operational_certification",
            "list_corporate_documents",
            "publish_corporate_html",
            "package_corporate_document",
        ]
        for method in mandatory:
            self.assertTrue(hasattr(self.studio, method), f"Missing method: {method}")
            self.assertTrue(callable(getattr(self.studio, method)))

    def test_repository_wrappers_smoke(self) -> None:
        docs = self.studio.list_documents()
        self.assertIsInstance(docs, list)
        stats = self.studio.statistics()
        self.assertIsInstance(stats, dict)
        search = self.studio.search("automation", limit=5)
        self.assertIsInstance(search, list)

    def test_repository_catalog_and_themes(self) -> None:
        catalog = self.studio.get_repository_catalog()
        self.assertIsInstance(catalog, dict)
        self.assertIn("repositories", catalog)

        themes = self.studio.theme_profiles()
        self.assertEqual(themes.get("default"), "ingecart_industrial")
        self.assertIn("service_engine", themes.get("available", []))

        assets = self.studio.resolve_asset_candidates(limit=5)
        self.assertIsInstance(assets, list)


if __name__ == "__main__":
    unittest.main()
