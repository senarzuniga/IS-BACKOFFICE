import unittest
import tempfile
from pathlib import Path

from soc.brain.memory_store import MemoryStore
from soc.brain.context_router import ContextRouter


class TestContextRouter(unittest.TestCase):

    def test_resolve_company(self):
        tmp = Path(tempfile.mkdtemp())
        db = tmp / 'mem.db'
        store = MemoryStore(db_path=db)
        cid = store.add_company('Ingecart')
        router = ContextRouter(store)
        c = router.resolve('Ingecart')
        self.assertIsNotNone(c)
        self.assertEqual(c['uuid'], cid)
        self.assertIsNone(router.resolve('NoSuchCompany'))


if __name__ == '__main__':
    unittest.main()
