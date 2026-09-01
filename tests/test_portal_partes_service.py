import unittest

from services.portal_partes_service import analyze_portal_partes, load_portal_partes_html, portal_partes_path


class PortalPartesServiceTests(unittest.TestCase):
    def test_portal_file_exists_and_loads(self):
        path = portal_partes_path()
        self.assertTrue(path.exists())
        self.assertIn("Portal de Partes de Horas", load_portal_partes_html(path))

    def test_analysis_detects_expected_capabilities(self):
        analysis = analyze_portal_partes()
        self.assertEqual("INGECART · Portal de Partes de Horas", analysis.title)
        self.assertEqual(["Nuevo parte", "Consulta por OF", "Configuración", "Base de datos"], analysis.tabs)
        self.assertEqual(["parte", "consulta", "config", "datos"], analysis.panel_ids)
        self.assertGreaterEqual(analysis.default_category_count, 10)
        self.assertIn("Sincronizacion de fichero JSON con OneDrive mediante File System Access API", analysis.persistence_modes)
        self.assertTrue(any("Registro de partes" in item for item in analysis.capabilities))
        self.assertTrue(any("SharePoint/Microsoft Graph" in item for item in analysis.limitations))


if __name__ == "__main__":
    unittest.main()
