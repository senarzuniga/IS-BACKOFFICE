import unittest
import time
import tempfile
from pathlib import Path

from soc.brain.demo_dataset import build_demo_store
from soc.brain.context_router import ContextRouter
from soc.brain.local_search import LocalSearch
from soc.brain.ai_orchestrator import AIOrchestrator


class TestPerformanceBaseline(unittest.TestCase):

    def test_generate_performance_baseline(self):
        tmp = Path(tempfile.mkdtemp())
        db = tmp / 'perf.db'
        store, mapping = build_demo_store(db_path=db)

        cr = ContextRouter(store)
        ls = LocalSearch(store)
        orch = AIOrchestrator(cr, ls)

        M = 30
        # Memory lookup latency
        t0 = time.perf_counter()
        for _ in range(M):
            cr.resolve('Ingecart')
        t_lookup = (time.perf_counter() - t0) / M

        # Local search latency
        t0 = time.perf_counter()
        for _ in range(M):
            ls.search(mapping['Ingecart'], 'project', limit=5)
        t_search = (time.perf_counter() - t0) / M

        # Orchestrator execution time
        t0 = time.perf_counter()
        for _ in range(5):
            orch.run('Ingecart', 'What are risks?', k=5)
        t_orch = (time.perf_counter() - t0) / 5

        # SQLite search performance
        t0 = time.perf_counter()
        for _ in range(M):
            store.search_documents(company_uuid=mapping['Ingecart'], query='project', limit=5)
        t_sql = (time.perf_counter() - t0) / M

        perf_path = Path.cwd() / 'PERFORMANCE_BASELINE.md'
        lines = [
            '# Performance Baseline',
            '',
            f'- Memory lookup latency (avg): {t_lookup*1000:.3f} ms',
            f'- Local search latency (avg): {t_search*1000:.3f} ms',
            f'- Orchestrator execution time (avg): {t_orch*1000:.3f} ms',
            f'- SQLite search (avg): {t_sql*1000:.3f} ms',
        ]
        perf_path.write_text('\n'.join(lines), encoding='utf8')
        self.assertTrue(perf_path.exists())


if __name__ == '__main__':
    unittest.main()
