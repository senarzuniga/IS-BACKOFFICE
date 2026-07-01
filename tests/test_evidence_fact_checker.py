import unittest

from soc.brain.evidence import collect_evidence
from soc.brain.fact_checker import assess_evidence


class TestEvidenceAndFactChecker(unittest.TestCase):

    def test_collect_and_assess(self):
        mem = [{'uuid': 'a', 'file_name': 'doc1', 'summary': 'apple orange', 'last_modified': 1, 'confidence': 0.9}]
        local = [
            {'doc_uuid': 'b', 'file': 'doc2', 'summary': 'banana', 'last_modified': 2, 'confidence': 0.8},
            {'doc_uuid': 'a', 'file': 'doc1', 'summary': 'apple pie', 'last_modified': 1.5, 'confidence': 0.85},
        ]

        merged = collect_evidence(mem, local, top_k=10)
        uuids = [e['doc_uuid'] for e in merged]
        self.assertIn('a', uuids)
        self.assertIn('b', uuids)

        assessment = assess_evidence(merged)
        self.assertIn('overall_confidence', assessment)
        self.assertIsInstance(assessment['overall_confidence'], float)


if __name__ == '__main__':
    unittest.main()
