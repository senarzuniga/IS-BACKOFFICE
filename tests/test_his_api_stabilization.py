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


if __name__ == "__main__":
    unittest.main()
