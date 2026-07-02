import unittest
import tempfile
from pathlib import Path

from soc.brain.memory_store import MemoryStore
from soc.brain.local_search import LocalSearch
from soc.brain.context_router import ContextRouter
from soc.brain.ai_orchestrator import AIOrchestrator


class TestAIOrchestrator(unittest.TestCase):

    def test_run_produces_structured_response(self):
        tmp = Path(tempfile.mkdtemp())
        db = tmp / 'mem.db'
        store = MemoryStore(db_path=db)
        cid = store.add_company('Ingecart')
        store.add_document(cid, 'r1.txt', 'The product supports high throughput and precision.')

        ls = LocalSearch(store)
        cr = ContextRouter(store)
        orch = AIOrchestrator(cr, ls)
        res = orch.run('Ingecart', 'What are the main risks?', k=3)

        self.assertEqual(res['company'], 'Ingecart')
        self.assertIn('llm', res)
        self.assertIsInstance(res['evidence'], list)
        self.assertIn('assessment', res)
        self.assertIn('executive_summary', res['llm'])


if __name__ == '__main__':
    unittest.main()
