import os
import sys
import unittest

# ensure repo root is on path when running tests as scripts
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from agents.competitive_intelligence.utils.scraper import extract_text_and_snippets


class ScraperTest(unittest.TestCase):
    def test_extract_simple_html(self):
        html = """
        <html><head><title>Acme</title></head>
        <body><p>First paragraph about automation and retrofit.</p><p>Second paragraph with more details.</p></body></html>
        """
        out = extract_text_and_snippets(html)
        self.assertIn('First paragraph', out['text'])
        # snippets may be small in short test HTML; ensure key fields exist
        self.assertIsInstance(out.get('snippets'), list)
        self.assertIsInstance(out.get('text'), str)


if __name__ == '__main__':
    unittest.main()
