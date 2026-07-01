import unittest
import tempfile
from pathlib import Path

from soc.brain.demo_dataset import build_demo_store
from soc.brain.local_search import LocalSearch
from soc.brain.context_router import ContextRouter
from soc.brain.ai_orchestrator import AIOrchestrator


class TestIntegrationPipeline(unittest.TestCase):

    def test_full_pipeline_company_isolation_and_evidence(self):
        tmp = Path(tempfile.mkdtemp())
        db = tmp / 'demo.db'
        store, mapping = build_demo_store(db_path=db)

        cr = ContextRouter(store)
        ls = LocalSearch(store)
        orch = AIOrchestrator(cr, ls)

        # Query Ingecart and ensure returned evidence belongs to Ingecart
        res = orch.run('Ingecart', 'Evaluate decisions', k=5)
        self.assertEqual(res['company_uuid'], mapping['Ingecart'])

        for e in res['evidence']:
            doc = store.get_document(e['doc_uuid'])
            # documents created for demo dataset are stored under company_uuid
            self.assertIsNotNone(doc)
            self.assertEqual(doc['company_uuid'], mapping['Ingecart'])

        # Search for IAR docs should not appear in Ingecart queries
        res_iar = orch.run('Industrial Augmented Reality', 'Evaluate decisions', k=5)
        self.assertEqual(res_iar['company_uuid'], mapping['Industrial Augmented Reality'])


if __name__ == '__main__':
    unittest.main()
