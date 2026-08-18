import copy
import unittest

from core.ingetrans_reference import (
    ReferenceValidationError,
    load_reference,
    validate_reference,
)


class IngetransReferenceTests(unittest.TestCase):
    def test_blocked_reference_is_valid_but_contains_no_promoted_values(self):
        reference = load_reference()

        self.assertEqual("BLOCKED_SOURCE_MISSING", reference["status"])
        self.assertEqual([], reference["parameters"])

    def test_level_one_requires_document_page_and_table(self):
        reference = load_reference()
        invalid = copy.deepcopy(reference)
        invalid["parameters"] = [
            {
                "variable": "cycle_time",
                "value": 52,
                "unit": "s",
                "governance_level": 1,
                "applicability": "PROJECT-SPECIFIC",
                "source_document": "Sterner.pdf",
                "source_page": None,
                "source_table": None,
                "source_condition": "unspecified",
                "confidence": 0.5,
                "validation_status": "PENDING",
                "effective_version": "1.0.0",
                "created_at": "2026-08-16T00:00:00Z",
                "updated_at": "2026-08-16T00:00:00Z"
            }
        ]

        with self.assertRaises(ReferenceValidationError):
            validate_reference(invalid)


if __name__ == "__main__":
    unittest.main()