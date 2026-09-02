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
        self.assertIn("Sincronizacion de JSON en GitHub Contents API", analysis.persistence_modes)
        self.assertTrue(any("Registro de partes" in item for item in analysis.capabilities))
        self.assertTrue(any("token de escritura GitHub" in item for item in analysis.limitations))

    def test_portal_includes_developer_role_and_restrictions(self):
        html = load_portal_partes_html()
        self.assertIn('data-tab="datos" data-dev', html)
        self.assertIn('<option value="developer">Developer</option>', html)
        self.assertIn("function requireDeveloperAction()", html)
        self.assertIn("Acción solo disponible para Developer", html)
        self.assertIn("const canConfig=admin||dev;", html)
        self.assertIn("Configuración requiere perfil Admin o Developer", html)
        self.assertIn("Token GitHub inválido", html)


if __name__ == "__main__":
    unittest.main()
