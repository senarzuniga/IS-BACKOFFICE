import os
import tempfile
import unittest

from pathlib import Path


class CompetitiveIntelTests(unittest.TestCase):
    def test_index_and_search(self):
        from knowledge_hub.competitive_intel.indexer import Indexer

        tmp = tempfile.TemporaryDirectory()
        dbp = Path(tmp.name) / 'test_ci.db'
        idx = Indexer(db_path=dbp)

        cid = idx.add_company('TestCo', seed_url='https://testco.example')
        sid = idx.add_source(cid, 'https://testco.example/product', type='web')
        doc_id = idx.add_document(cid, sid, 'product.md', 'TestCo product reel handling and automation')

        results = idx.search_by_company_name('TestCo', 'reel')
        self.assertTrue(len(results) >= 1)
        self.assertIn('reel', results[0]['summary'].lower())

        tmp.cleanup()

    def test_graph_and_scores(self):
        from knowledge_hub.competitive_intel.graph import KnowledgeGraph
        from knowledge_hub.competitive_intel.score import compute_scores

        g = KnowledgeGraph()
        g.add_node('Ingecart', type='Company')
        g.add_node('DGM', type='Company')
        g.add_edge('Ingecart', 'competes_with', 'DGM', weight=0.8)

        neigh = g.neighbors('Ingecart')
        self.assertIn('DGM', neigh)

        profile = {'capabilities': ['reel handling'], 'technologies': ['servo'], 'markets': ['Europe']}
        scores = compute_scores(profile)
        self.assertIn('market_strength', scores)
        self.assertGreaterEqual(scores['market_strength'], 0.0)


if __name__ == '__main__':
    unittest.main()
