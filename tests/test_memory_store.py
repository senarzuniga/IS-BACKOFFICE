import unittest
import tempfile
from pathlib import Path

from soc.brain.memory_store import MemoryStore


class TestMemoryStore(unittest.TestCase):

    def test_company_and_document_crud(self):
        tmp = Path(tempfile.mkdtemp())
        db = tmp / 'mem.db'
        store = MemoryStore(db_path=db)

        # Company
        cid = store.add_company('Ingecart', source_ref='unit', owner='tester')
        self.assertIsInstance(cid, str)
        comp = store.get_company_by_name('Ingecart')
        self.assertIsNotNone(comp)
        self.assertEqual(comp['name'], 'Ingecart')

        # Documents
        docid = store.add_document(cid, 'doc1.txt', 'This document mentions widget and throughput', file_path='/tmp/doc1')
        self.assertIsInstance(docid, str)
        got = store.get_document(docid)
        self.assertIsNotNone(got)
        self.assertEqual(got['file_name'], 'doc1.txt')

        # Search should return the document for the company
        results = store.search_documents(company_uuid=cid, query='widget', limit=5)
        self.assertTrue(any(r['uuid'] == docid for r in results))

        # Decisions and AI queries
        did = store.add_decision(cid, 'Test Decision', 'Approve testing', source_ref='unit')
        self.assertIsInstance(did, str)
        qid = store.record_ai_query(cid, 'What is the status?', 'No status yet')
        self.assertIsInstance(qid, str)


if __name__ == '__main__':
    unittest.main()
