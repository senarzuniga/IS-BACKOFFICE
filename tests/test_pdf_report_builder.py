import base64
import unittest
from datetime import datetime

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    fitz = None


@unittest.skipUnless(fitz is not None, "PyMuPDF is required for PDF export tests")
class TestPDFReportBuilder(unittest.TestCase):
    def test_build_pdf_with_title_date_and_pagination(self):
        from document_analysis.pdf_report_builder import PDFReportBuilder

        content = (
            "# Informe Ejecutivo\n\n"
            "## Resumen\n"
            "- Punto clave 1\n"
            "- Punto clave 2\n\n"
            "```python\n"
            "def hello():\n"
            "    return 'ok'\n"
            "```\n"
        )
        created_at = datetime(2026, 5, 9, 8, 0, 0)

        pdf_bytes = PDFReportBuilder().build_pdf(
            content,
            title="Informe IAR FESPA",
            created_at=created_at,
            source_type="TXT",
        )

        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        self.assertGreaterEqual(doc.page_count, 1)
        full_text = "\n".join(page.get_text() for page in doc)
        doc.close()

        self.assertIn("Informe IAR FESPA", full_text)
        self.assertIn("Fecha de creación:", full_text)
        self.assertIn("Página 1 de", full_text)

    def test_build_pdf_supports_header_image(self):
        from document_analysis.pdf_report_builder import PDFReportBuilder

        tiny_png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7+N3kAAAAASUVORK5CYII="
        )

        pdf_bytes = PDFReportBuilder().build_pdf(
            "Contenido de prueba",
            title="Informe con logo",
            created_at=datetime(2026, 5, 9, 8, 15, 0),
            header_image_bytes=tiny_png,
            source_type="CODE",
        )

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        self.assertGreaterEqual(doc.page_count, 1)
        self.assertEqual(doc.metadata.get("author"), "IS-BACKOFFICE")
        doc.close()
