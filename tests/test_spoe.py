import unittest
from datetime import date
from pathlib import Path

from backoffice.spoe.architecture import evaluate_architecture_alternatives
from backoffice.spoe.calculator import calculate_sr1400_bom
from backoffice.spoe.coordinator import supervise_offer_quality
from backoffice.spoe.documents import generate_offer_documents
from backoffice.spoe.knowledge import build_knowledge_package
from backoffice.spoe.models import OfferInput


class TestSPOE(unittest.TestCase):
    def _sample_offer(self) -> OfferInput:
        return OfferInput(
            customer="ACME Corrugated",
            plant="Plant A",
            country="Spain",
            language="es",
            offer_number="OFF-TEST-001",
            offer_date=date(2026, 7, 23),
            project_name="SR1400 Deployment",
            total_main_line_length_m=120.0,
            turns_90=4,
            ramps_count=2,
            ramp_lengths_m=[8.0, 10.0],
            additional_notes="n/a",
            commercial_notes="n/a",
            technical_notes="n/a",
            layout_image_path="layout.png",
            optional_attachment_paths=["a.pdf"],
        )

    def test_bom_rounds_up_and_has_components(self):
        bom = calculate_sr1400_bom(self._sample_offer())
        self.assertIn("Chains", bom)
        self.assertIn("Motors", bom)
        self.assertGreaterEqual(bom["Chains"], 1)
        self.assertIsInstance(bom["Chains"], int)

    def test_architecture_selects_best_alternative(self):
        data = evaluate_architecture_alternatives()
        self.assertEqual(data["selected"]["name"], "A2 | Framework Extension (Chosen)")

    def test_quality_supervision_reaches_acceptance(self):
        offer = self._sample_offer()
        bom = calculate_sr1400_bom(offer)
        quality = supervise_offer_quality(offer, bom, [
            "Commercial Offer",
            "Technical Proposal",
            "Executive Summary",
            "Bill of Materials",
            "Scope of Supply",
            "Excluded Scope",
            "Installation Estimate",
            "Commissioning",
            "Commercial Conditions",
            "General Terms",
            "Engineering Annex",
        ])
        self.assertTrue(quality.accepted)
        self.assertGreaterEqual(quality.quality_score, 90.0)

    def test_docx_generation_outputs_files(self):
        offer = self._sample_offer()
        bom = calculate_sr1400_bom(offer)
        knowledge = build_knowledge_package(offer)
        docs = generate_offer_documents(offer, bom, knowledge)
        self.assertIn("Commercial Offer", docs)
        self.assertTrue(Path(docs["Commercial Offer"]).exists())


if __name__ == "__main__":
    unittest.main()
