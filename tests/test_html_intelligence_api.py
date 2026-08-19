from __future__ import annotations

import unittest

from fastapi import HTTPException

from api.routes.html_intelligence import document, status
from main import app


class TestHtmlIntelligenceApi(unittest.TestCase):
    def test_status_exposes_authorized_repositories_and_formats(self) -> None:
        payload = status()
        self.assertEqual(payload["status"], "operational")
        self.assertEqual(set(payload["repositories"]), {"ai_factory", "adaptive_sales_engine", "ingesite"})
        self.assertEqual(payload["formats"], ["html", "pdf", "docx", "xlsx", "pptx"])
        paths = {route.path for route in app.routes}
        self.assertIn("/html-intelligence/status", paths)
        self.assertIn("/html-intelligence/documents", paths)

    def test_unknown_document_returns_404(self) -> None:
        with self.assertRaises(HTTPException) as caught:
            document("not-found")
        self.assertEqual(caught.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()