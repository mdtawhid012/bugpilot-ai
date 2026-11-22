import unittest

from app.integrations.ai.fake_provider import FakeProvider
from app.integrations.ai.protocols import InvestigationContext
from app.models.evidence import ContentType, EvidenceKind, ProducerKind


class FakeProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = FakeProvider()
        self.context = InvestigationContext(
            investigation_id="investigation-1",
            report="The discount calculation gives the wrong result.",
            fixture_id="discount-calculator",
            fixture_title="Discount calculator",
            fixture_language="python",
            fixture_revision="synthetic-v1",
            source_path="fixtures/discount_calculator/calculator.py",
            source_content="def apply_discount(price: float, percentage: float) -> float:\n    return price - percentage\n",
            source_line_start=1,
            source_line_end=2,
            source_revision="synthetic-v1",
            source_content_hash="9c8b2223223dce44fe1e8f7c526f19f34051e559f69a63f21e894eba11999824",
        )

    def test_output_is_deterministic_and_uses_approved_provenance(self) -> None:
        first = self.provider.generate(self.context)
        second = self.provider.generate(self.context)

        self.assertEqual([item.id for item in first], [item.id for item in second])
        self.assertEqual(
            [item.kind for item in first],
            [
                EvidenceKind.SOURCE_REFERENCE,
                EvidenceKind.HYPOTHESIS,
                EvidenceKind.TEST_PROPOSAL,
                EvidenceKind.PATCH_PROPOSAL,
            ],
        )
        for item in first:
            self.assertEqual(item.source_fixture_id, "discount-calculator")
            self.assertEqual(item.source_ref["path"], "fixtures/discount_calculator/calculator.py")

        hypothesis = first[1]
        test = first[2]
        patch = first[3]
        self.assertEqual(hypothesis.content_type, ContentType.GENERATED)
        self.assertEqual(hypothesis.producer_kind, ProducerKind.FAKE_PROVIDER)
        self.assertIn("Unconfirmed hypothesis", hypothesis.summary)
        self.assertEqual(test.content_type, ContentType.GENERATED)
        self.assertIn("Proposal only", test.summary)
        self.assertNotIn("reproduced", test.summary.lower())
        self.assertEqual(patch.content_type, ContentType.GENERATED)
        self.assertIn("no source file is modified", patch.summary.lower())
        self.assertIn("Diff proposal", patch.summary)

    def test_provider_rejects_context_outside_fixture_root(self) -> None:
        unsafe = InvestigationContext(
            investigation_id="investigation-1",
            report="Wrong behavior",
            fixture_id="discount-calculator",
            fixture_title="Discount calculator",
            fixture_language="python",
            fixture_revision="synthetic-v1",
            source_path="../outside.py",
            source_content="print('outside')",
            source_line_start=1,
            source_line_end=1,
            source_revision="synthetic-v1",
            source_content_hash="0" * 64,
        )
        with self.assertRaises(ValueError):
            self.provider.generate(unsafe)

    def test_provider_rejects_oversized_report_and_source(self) -> None:
        oversized_report = InvestigationContext(**{**self.context.__dict__, "report": "x" * (16 * 1024 + 1)})
        with self.assertRaises(ValueError):
            self.provider.generate(oversized_report)

        oversized_source = InvestigationContext(**{**self.context.__dict__, "source_content": "x" * (64 * 1024 + 1)})
        with self.assertRaises(ValueError):
            self.provider.generate(oversized_source)
