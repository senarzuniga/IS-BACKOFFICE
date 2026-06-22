import os
import sys
import unittest

# ensure repo root is on path when running tests as scripts
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.run_demo import main as run_demo_main


class AgentsSmokeTest(unittest.TestCase):
    def test_run_demo_no_web_creates_report(self):
        # run the demo script in no-web mode (programmatic invocation)
        os.system('python scripts/run_demo.py --company TEST_COMPANY --no-web')
        # check reports folder
        reports_dir = os.path.join('data', 'competitive_intelligence', 'reports')
        self.assertTrue(os.path.exists(reports_dir))


if __name__ == '__main__':
    unittest.main()
