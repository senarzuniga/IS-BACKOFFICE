import unittest
import tempfile
import time
from pathlib import Path

from soc.brain.memory_store import MemoryStore
from soc.brain.local_search import LocalSearch


class TestLocalSearch(unittest.TestCase):

    def test_search_ranking_and_indexing(self):
        tmp = Path(tempfile.mkdtemp())
        db = tmp / 'mem.db'
        store = MemoryStore(db_path=db)
        cid = store.add_company('IAR', source_ref='unit')

        # Add documents with slight time differences to affect recency
        d1 = store.add_document(cid, 'd1.txt', 'alpha beta gamma alpha alpha')
        time.sleep(0.01)
        d2 = store.add_document(cid, 'd2.txt', 'alpha beta')

        ls = LocalSearch(store)
        res = ls.search(cid, 'alpha', limit=2)
        self.assertGreaterEqual(len(res), 1)
        self.assertIn('doc_uuid', res[0])
        self.assertIn('confidence', res[0])
        self.assertIsInstance(res[0]['confidence'], float)

        # index_document should add a new doc
        new_id = ls.index_document(cid, 'd3.txt', 'new content alpha')
        got = store.get_document(new_id)
        self.assertIsNotNone(got)


if __name__ == '__main__':
    unittest.main()
