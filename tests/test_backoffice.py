"""Comprehensive test suite for the IS-BACKOFFICE system."""
import unittest
from datetime import datetime, timezone


# ── Models ────────────────────────────────────────────────────────────────────

class TestModels(unittest.TestCase):

    def test_base_entity_defaults(self):
        from backoffice.models.base import BaseEntity
        e = BaseEntity()
        self.assertIsNotNone(e.id)
        self.assertAlmostEqual(e.confidence, 1.0)
        self.assertFalse(e.needs_review)

    def test_source_trace(self):
        from backoffice.models.base import SourceTrace
        st = SourceTrace(source_type="pdf", file_path="/tmp/doc.pdf")
        self.assertEqual(st.source_type, "pdf")
        self.assertEqual(st.file_path, "/tmp/doc.pdf")

    def test_client(self):
        from backoffice.models.client import Client
        c = Client(name="Acme Corp")
        self.assertEqual(c.name, "Acme Corp")
        self.assertEqual(c.currency, "EUR")

    def test_offer(self):
        from backoffice.models.offer import Offer
        o = Offer(client_id="c1", title="Offer A", total_value=50000.0)
        self.assertEqual(o.total_value, 50000.0)
        self.assertEqual(o.status, "draft")

    def test_sale(self):
        from backoffice.models.sale import Sale
        s = Sale(client_id="c1", amount=12345.0)
        self.assertFalse(s.validated)

    def test_opportunity(self):
        from backoffice.models.opportunity import Opportunity
        op = Opportunity(client_id="c1", title="Big Deal")
        self.assertEqual(op.stage, "qualification")

    def test_product(self):
        from backoffice.models.product import Product
        p = Product(name="Consulting Service")
        self.assertEqual(p.lifecycle_stage, "active")


# ── Ingestion ─────────────────────────────────────────────────────────────────

class TestIngestion(unittest.TestCase):

    def test_email_connector_dict(self):
        from backoffice.ingestion.email_connector import EmailConnector
        conn = EmailConnector()
        records = conn.ingest({
            "subject": "Offer for Client ABC",
            "sender": "sales@example.com",
            "body": "Dear client, please find our offer attached.",
        })
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].source_type, "email")
        self.assertIn("offer", records[0].raw_text.lower())

    def test_email_document_class_offer(self):
        from backoffice.ingestion.email_connector import EmailConnector
        conn = EmailConnector()
        records = conn.ingest({"subject": "New Offer", "body": "Our offer is ready", "sender": ""})
        self.assertEqual(records[0].document_class, "offer")

    def test_txt_connector(self):
        from backoffice.ingestion.txt_connector import TxtConnector
        conn = TxtConnector()
        records = conn.ingest(b"Hello world contract text")
        self.assertEqual(records[0].source_type, "txt")
        self.assertIsNotNone(records[0].checksum)

    def test_checksum_computed(self):
        from backoffice.ingestion.base import RawRecord
        cs = RawRecord.compute_checksum(b"test")
        self.assertEqual(len(cs), 64)  # SHA-256 hex digest

    def test_document_class_detection_contract(self):
        from backoffice.ingestion.base import BaseConnector
        class MockConn(BaseConnector):
            @property
            def source_type(self): return "mock"
            def ingest(self, source): return []
        mc = MockConn()
        self.assertEqual(mc._detect_document_class("This is a contract agreement"), "contract")
        self.assertEqual(mc._detect_document_class("Invoice number 123"), "invoice")
        self.assertEqual(mc._detect_document_class("Random text"), "other")


# ── Cleaning ──────────────────────────────────────────────────────────────────

class TestCleaning(unittest.TestCase):

    def test_normalizer_name(self):
        from backoffice.cleaning.normalizer import Normalizer
        n = Normalizer()
        self.assertEqual(n.normalize_name("  Société Générale  "), "societe generale")

    def test_normalizer_parse_number_us(self):
        from backoffice.cleaning.normalizer import Normalizer
        n = Normalizer()
        self.assertAlmostEqual(n.parse_number("1,234.56"), 1234.56)

    def test_normalizer_parse_number_eu(self):
        from backoffice.cleaning.normalizer import Normalizer
        n = Normalizer()
        self.assertAlmostEqual(n.parse_number("1.234,56"), 1234.56)

    def test_convert_to_eur(self):
        from backoffice.cleaning.normalizer import Normalizer
        n = Normalizer()
        result = n.convert_to_eur(100.0, "USD")
        self.assertAlmostEqual(result, 92.0)

    def test_deduplicator(self):
        from backoffice.ingestion.base import RawRecord
        from backoffice.cleaning.deduplicator import Deduplicator
        r1 = RawRecord(source_type="txt", checksum="abc123")
        r2 = RawRecord(source_type="txt", checksum="abc123")  # duplicate
        r3 = RawRecord(source_type="txt", checksum="xyz999")
        dedup = Deduplicator()
        result = dedup.deduplicate_raw([r1, r2, r3])
        self.assertEqual(len(result), 2)

    def test_validator_number(self):
        from backoffice.cleaning.validator import Validator
        v = Validator()
        ok, errs = v.validate_number(100.0)
        self.assertTrue(ok)
        ok2, errs2 = v.validate_number(-5.0)
        self.assertFalse(ok2)

    def test_validator_email(self):
        from backoffice.cleaning.validator import Validator
        v = Validator()
        ok, _ = v.validate_email("test@example.com")
        self.assertTrue(ok)
        ok2, _ = v.validate_email("not-an-email")
        self.assertFalse(ok2)

    def test_cleaning_pipeline(self):
        from backoffice.ingestion.email_connector import EmailConnector
        from backoffice.cleaning.pipeline import CleaningPipeline
        conn = EmailConnector()
        records = conn.ingest({"subject": "Test", "body": "Content", "sender": "a@b.com"})
        # Duplicate
        records = records + records
        pipeline = CleaningPipeline()
        cleaned, report = pipeline.run(records)
        self.assertEqual(report.total_in, 2)
        self.assertEqual(report.duplicates_removed, 1)
        self.assertEqual(len(cleaned), 1)


# ── Extraction ────────────────────────────────────────────────────────────────

class TestExtraction(unittest.TestCase):

    def _make_record(self, text: str):
        from backoffice.ingestion.base import RawRecord
        return RawRecord(source_type="txt", raw_text=text,
                         checksum=RawRecord.compute_checksum(text.encode()))

    def test_extract_offer(self):
        from backoffice.extraction.engine import ExtractionEngine
        eng = ExtractionEngine()
        rec = self._make_record("Offre n°2024-001 pour client ACME Corp. Montant: 50000 EUR")
        result = eng.extract(rec)
        self.assertEqual(result.record_id, rec.record_id)
        self.assertGreater(len(result.offers), 0)

    def test_extract_email(self):
        from backoffice.extraction.engine import ExtractionEngine
        eng = ExtractionEngine()
        rec = self._make_record("Contact: john.doe@acme.com, phone +33 1 23 45 67 89")
        result = eng.extract(rec)
        self.assertGreater(len(result.contacts), 0)

    def test_review_queue(self):
        from backoffice.extraction.engine import ExtractionEngine, ExtractionResult
        from backoffice.extraction.review_queue import ReviewQueue
        q = ReviewQueue()
        result = ExtractionResult(record_id="test-id", needs_review=True, review_reasons=["test"])
        item = q.enqueue(result)
        self.assertEqual(len(q.pending()), 1)
        q.approve(item.item_id, "looks good")
        self.assertEqual(len(q.pending()), 0)


# ── Graph ─────────────────────────────────────────────────────────────────────

class TestGraph(unittest.TestCase):

    def setUp(self):
        from backoffice.graph.store import GraphStore
        self.store = GraphStore()

    def test_upsert_client(self):
        from backoffice.models.client import Client
        c = Client(name="Test Corp")
        self.store.upsert_client(c)
        self.assertEqual(len(self.store.get_all_clients()), 1)
        self.assertEqual(self.store.get_client(c.id).name, "Test Corp")

    def test_add_relation(self):
        from backoffice.graph.relations import Relation, RelationType
        r = Relation(
            relation_type=RelationType.CLIENT_HAS_OFFER,
            source_id="client-1",
            target_id="offer-1",
        )
        self.store.add_relation(r)
        rels = self.store.get_relations_for("client-1")
        self.assertEqual(len(rels), 1)

    def test_client_timeline(self):
        from backoffice.models.client import Client
        from backoffice.models.sale import Sale
        from datetime import datetime, timezone
        c = Client(name="Timeline Corp")
        self.store.upsert_client(c)
        s = Sale(client_id=c.id, amount=5000.0, sale_date=datetime.now(timezone.utc))
        self.store.upsert_sale(s)
        tl = self.store.get_client_timeline(c.id)
        self.assertEqual(len(tl["sales"]), 1)

    def test_semantic_search(self):
        from backoffice.models.client import Client
        from backoffice.graph.search import SemanticSearch
        c = Client(name="Renault Automotive")
        self.store.upsert_client(c)
        searcher = SemanticSearch(self.store)
        results = searcher.search("automotive")
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["type"], "client")

    def test_stats(self):
        stats = self.store.stats()
        self.assertIn("clients", stats)
        self.assertIn("relations", stats)


# ── Analytics ─────────────────────────────────────────────────────────────────

class TestAnalytics(unittest.TestCase):

    def setUp(self):
        from backoffice.graph.store import GraphStore
        from backoffice.models.client import Client
        from backoffice.models.opportunity import Opportunity
        from backoffice.models.sale import Sale
        from backoffice.models.offer import Offer
        from backoffice.models.product import Product
        from datetime import datetime, timezone

        self.store = GraphStore()
        c = Client(name="Megacorp SA")
        self.store.upsert_client(c)
        self.client_id = c.id

        for stage, val in [("proposal", 100000), ("negotiation", 200000), ("closed_won", 50000)]:
            self.store.upsert_opportunity(Opportunity(
                client_id=c.id, title=f"Deal-{stage}", stage=stage, estimated_value=val
            ))

        for amount, month in [(30000, "2024-01"), (40000, "2024-02"), (55000, "2024-03")]:
            self.store.upsert_sale(Sale(
                client_id=c.id, amount=float(amount), amount_eur=float(amount),
                sale_date=datetime(2024, int(month.split("-")[1]), 15, tzinfo=timezone.utc)
            ))

        self.store.upsert_offer(Offer(client_id=c.id, title="Offer X", total_value=120000.0))

        p = Product(name="Flagship Product")
        self.store.upsert_product(p)
        self.product_id = p.id

    def test_pipeline_summary(self):
        from backoffice.analytics.pipeline_scoring import PipelineScorer
        summary = PipelineScorer(self.store).pipeline_summary()
        self.assertIn("total_opportunities", summary)
        self.assertGreater(summary["total_weighted_pipeline_eur"], 0)

    def test_forecast(self):
        from backoffice.analytics.forecasting import Forecaster
        f = Forecaster(self.store)
        monthly = f.monthly_revenue()
        self.assertEqual(len(monthly), 3)
        forecast = f.forecast_next_period(periods=3)
        self.assertIn("forecasted_periods", forecast)
        self.assertEqual(len(forecast["forecasted_periods"]), 3)

    def test_conversion_probability(self):
        from backoffice.analytics.forecasting import Forecaster
        conv = Forecaster(self.store).conversion_probability()
        self.assertIn("conversion_probability", conv)

    def test_account_health(self):
        from backoffice.analytics.account_health import AccountHealthScorer
        health = AccountHealthScorer(self.store).score_client(self.client_id)
        self.assertIn("health_score", health)
        self.assertGreaterEqual(health["health_score"], 0)

    def test_offer_validation(self):
        from backoffice.analytics.offer_validation import OfferValidator
        results = OfferValidator(self.store).validate_all_offers()
        self.assertEqual(len(results), 1)
        self.assertIn("is_valid", results[0])

    def test_portfolio(self):
        from backoffice.analytics.portfolio import PortfolioAnalyzer
        products = PortfolioAnalyzer(self.store).classify_products()
        self.assertEqual(len(products), 1)
        self.assertIn("lifecycle_stage", products[0])


# ── Reporting ─────────────────────────────────────────────────────────────────

class TestReporting(unittest.TestCase):

    def setUp(self):
        from backoffice.graph.store import GraphStore
        from backoffice.models.client import Client
        self.store = GraphStore()
        c = Client(name="Report Client")
        self.store.upsert_client(c)
        self.client_id = c.id

    def test_executive_summary(self):
        from backoffice.reporting.generator import ReportGenerator
        report = ReportGenerator(self.store).executive_summary()
        self.assertEqual(report["report_type"], "executive_summary")
        self.assertIn("graph_stats", report)
        self.assertIn("pipeline", report)

    def test_client_diagnostic(self):
        from backoffice.reporting.generator import ReportGenerator
        report = ReportGenerator(self.store).client_diagnostic(self.client_id)
        self.assertEqual(report["report_type"], "client_diagnostic")
        self.assertIn("health", report)

    def test_to_json(self):
        from backoffice.reporting.generator import ReportGenerator
        gen = ReportGenerator(self.store)
        report = gen.executive_summary()
        json_str = gen.to_json(report)
        self.assertIn("executive_summary", json_str)

    def test_to_html(self):
        from backoffice.reporting.generator import ReportGenerator
        gen = ReportGenerator(self.store)
        report = gen.executive_summary()
        html = gen.to_html(report)
        self.assertIn("<html>", html)
        self.assertIn("Executive Summary", html)


if __name__ == "__main__":
    unittest.main()
