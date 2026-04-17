import unittest

from backoffice import CommercialIntelligenceOS


class BackOfficeSystemTests(unittest.TestCase):
    def test_closed_loop_cycle_and_traceability(self):
        osys = CommercialIntelligenceOS()
        records = [
            osys.ingestion.ingest_record(
                "outlook_email",
                "client=ACME;contact=ana@acme.com;offer=Digital Roadmap;price=25000;date=2026-01-10;opportunity=Plant modernization;value=80000",
                "mail-001",
                classification="offer",
            ),
            osys.ingestion.ingest_record(
                "excel",
                "client=ACME;sale=Phase1;product=Analytics Sprint;value=15000;date=2026-02-01",
                "excel-001",
                classification="sale",
            ),
            osys.ingestion.ingest_record(
                "excel",
                "client=ACME;sale=Phase1;product=Analytics Sprint;value=15000;date=2026-02-01",
                "excel-001",
                classification="sale",
            ),
        ]

        result = osys.run_cycle(records)

        self.assertEqual(result["processing"]["dropped_duplicates"], 1)
        self.assertGreaterEqual(result["knowledge_graph_nodes"], 3)
        self.assertGreaterEqual(result["knowledge_graph_edges"], 2)
        self.assertTrue(result["outputs"]["traceability"])
        self.assertIn("Plant modernization", result["learning_feedback"])
        self.assertIn("forecasting", result["analytics"])

    def test_offer_validation_anomaly_detection(self):
        osys = CommercialIntelligenceOS()
        records = [
            osys.ingestion.ingest_record(
                "txt",
                "client=Beta;offer=Premium package;price=999999;date=2026-01-01",
                "txt-001",
                classification="offer",
            ),
            osys.ingestion.ingest_record(
                "txt",
                "client=Beta;sale=Support;product=Support;value=1000;date=2026-01-15",
                "txt-002",
                classification="sale",
            ),
        ]

        result = osys.run_cycle(records)
        anomalies = result["analytics"]["offer_validation"]["anomalies"]

        self.assertEqual(len(anomalies), 1)
        self.assertFalse(result["analytics"]["offer_validation"]["consistency_ok"])


if __name__ == "__main__":
    unittest.main()
