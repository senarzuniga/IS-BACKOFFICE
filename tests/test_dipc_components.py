import unittest

from backoffice.dipc.component_library import normalize_component, render_component


class TestDipcComponents(unittest.TestCase):
    def test_timeline_renderer_outputs_svg(self):
        component = normalize_component(
            "timeline",
            "Project Roadmap",
            None,
            items=[
                {"title": "Phase 1", "body": "Discovery"},
                {"title": "Phase 2", "body": "Deployment"},
            ],
        )
        html = render_component(component)
        self.assertIn("<svg", html)
        self.assertIn("Phase 1", html)

    def test_hierarchy_renderer_outputs_tree_blocks(self):
        component = normalize_component(
            "hierarchy",
            "Org Chart",
            None,
            items=[
                {"title": "CEO", "body": "Executive"},
                {"title": "Engineering", "body": "Delivery"},
                {"title": "Operations", "body": "Execution"},
            ],
        )
        html = render_component(component)
        self.assertIn("dipc-tree-root", html)
        self.assertIn("Engineering", html)


if __name__ == "__main__":
    unittest.main()
