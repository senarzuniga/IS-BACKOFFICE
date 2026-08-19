from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from backoffice.his.corporate_models import DeliveryPolicy
from backoffice.his.corporate_publishing import CorporatePublishingService
from backoffice.his.repository_adapters import CorporateRepositorySettings


SAMPLE_HTML = """<!doctype html><html><body>
<header class="hero"><div class="lang lang-en"><h1>Audit report</h1><p>Decision evidence</p></div>
<div class="lang lang-es"><h1>Informe de auditoria</h1><p>Evidencia de decision</p></div></header>
<section id="decision"><div class="lang lang-en"><h2>Decision</h2><p>Validated result 25 kg.</p></div>
<div class="lang lang-es"><h2>Decision</h2><p>Resultado validado 25 kg.</p></div></section>
</body></html>"""


class TestHISCorporatePublishing(unittest.TestCase):
    def _settings(self, root: Path) -> CorporateRepositorySettings:
        ai_factory = root / "AI-FACTORY-v2"
        ai_factory.mkdir()
        (ai_factory / "source.html").write_text(SAMPLE_HTML, encoding="utf-8")
        ase = root / "adaptive-sales-engine"
        ase.mkdir()
        ingesite = root / "ingesite.github.io"
        ingesite.mkdir()
        output = root / "output"
        return CorporateRepositorySettings(
            ai_factory_root=ai_factory,
            adaptive_sales_engine_root=ase,
            ingesite_root=ingesite,
            ingesite_staging_root=output / "ingesite_staging",
            output_root=output,
            registry_path=output / "registry.json",
        )

    def test_publish_bilingual_html_and_build_pdf_only_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = CorporatePublishingService(self._settings(Path(tmp)))
            policy = DeliveryPolicy(
                profile_id="cascades_pdf_only",
                allowed_formats=["pdf"],
                required_languages=["en", "es"],
            )
            document = service.publish_bilingual_html(
                repository_id="ai_factory",
                relative_path="source.html",
                title="Corporate Audit",
                client="Cascades",
                project="Audit",
                delivery_policy=policy,
            )

            self.assertEqual(document.status, "ready")
            self.assertEqual({item.format for item in document.artifacts}, {"pdf"})
            self.assertEqual({item.language for item in document.artifacts}, {"en", "es"})
            package = Path(service.create_delivery_package(document.document_id))
            with zipfile.ZipFile(package) as archive:
                names = archive.namelist()
            self.assertIn("manifest.json", names)
            self.assertIn("validation_report.json", names)
            self.assertFalse(any(name.endswith((".html", ".docx")) for name in names))

            manifest = json.loads(Path(document.source_document_model).parents[1].joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["delivery_policy"]["profile_id"], "cascades_pdf_only")

    def test_generates_independent_xlsx_and_pptx_renderers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = CorporatePublishingService(self._settings(Path(tmp)))
            document = service.publish_bilingual_html(
                repository_id="ai_factory",
                relative_path="source.html",
                title="Editable Corporate Outputs",
                client="INGECART",
                project="Publishing",
                delivery_policy=DeliveryPolicy(
                    profile_id="editable",
                    allowed_formats=["xlsx", "pptx"],
                    required_languages=["en"],
                ),
            )
            self.assertEqual({item.format for item in document.artifacts}, {"xlsx", "pptx"})
            self.assertTrue(all(Path(item.path).stat().st_size > 1000 for item in document.artifacts))


if __name__ == "__main__":
    unittest.main()
