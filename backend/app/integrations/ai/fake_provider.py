import hashlib
import re
import uuid

from app.integrations.ai.protocols import InvestigationContext
from app.models.evidence import ContentType, EvidenceKind, EvidenceRecord, ProducerKind


class FakeProvider:
    version = "fixture-fake-v2"

    def generate(self, context: InvestigationContext) -> list[EvidenceRecord]:
        self._validate_context(context)
        seed = "|".join(
            (
                self.version,
                context.investigation_id,
                context.fixture_id,
                context.fixture_revision,
                context.source_content_hash,
                context.report,
            )
        )
        source_ref = {
            "path": context.source_path,
            "line_start": context.source_line_start,
            "line_end": context.source_line_end,
            "revision": context.source_revision,
            "content_hash": context.source_content_hash,
        }
        hypothesis_id = self._evidence_id(seed, "hypothesis")
        test_id = self._evidence_id(seed, "test_proposal")
        report = " ".join(context.report.split())

        return [
            EvidenceRecord(
                id=self._evidence_id(seed, "source_reference"),
                kind=EvidenceKind.SOURCE_REFERENCE,
                content_type=ContentType.OBSERVED,
                producer_kind=ProducerKind.FIXTURE,
                producer_version=context.fixture_revision,
                source_fixture_id=context.fixture_id,
                title="Curated fixture source",
                summary="Permitted source file metadata for the deterministic investigation context.",
                source_ref=source_ref,
            ),
            EvidenceRecord(
                id=hypothesis_id,
                kind=EvidenceKind.HYPOTHESIS,
                content_type=ContentType.GENERATED,
                producer_kind=ProducerKind.FAKE_PROVIDER,
                producer_version=self.version,
                source_fixture_id=context.fixture_id,
                title="Discount calculation may subtract the percentage",
                summary=(
                    "Unconfirmed hypothesis (confidence: 0.65). The report suggests incorrect discount behavior. "
                    "The curated implementation applies the percentage as a direct subtraction; verify whether "
                    "the fixture models percentage as a percentage of price."
                ),
                source_ref=source_ref,
            ),
            EvidenceRecord(
                id=test_id,
                kind=EvidenceKind.TEST_PROPOSAL,
                content_type=ContentType.GENERATED,
                producer_kind=ProducerKind.FAKE_PROVIDER,
                producer_version=self.version,
                source_fixture_id=context.fixture_id,
                title="Propose a 20 percent discount regression test",
                summary=(
                    "Proposal only; it is not executable or run. Intended behavior: a 20 percent discount on "
                    "100.0 should yield 80.0. Input conditions: price=100.0, percentage=20.0. "
                    f"Expected result: 80.0. Related hypothesis: {hypothesis_id}. Report context: {report}."
                ),
                source_ref=source_ref,
            ),
            EvidenceRecord(
                id=self._evidence_id(seed, "patch_proposal"),
                kind=EvidenceKind.PATCH_PROPOSAL,
                content_type=ContentType.GENERATED,
                producer_kind=ProducerKind.FAKE_PROVIDER,
                producer_version=self.version,
                source_fixture_id=context.fixture_id,
                title="Proposed percentage discount correction",
                summary=(
                    "Proposal only; no source file is modified. Affected file: fixtures/discount_calculator/calculator.py. "
                    "Intended modification: convert the percentage input into a fraction of price. "
                    "Reason: this addresses the suspected direct-subtraction issue. "
                    f"Related hypothesis: {hypothesis_id}. Related test proposal: {test_id}.\n"
                    "Diff proposal:\n"
                    "-    return price - percentage\n"
                    "+    return price * (1 - percentage / 100)"
                ),
                source_ref=source_ref,
            ),
        ]

    @staticmethod
    def _evidence_id(seed: str, kind: str) -> str:
        digest = hashlib.sha256(f"{seed}|{kind}".encode("utf-8")).digest()
        return str(uuid.UUID(bytes=digest[:16], version=5))

    @staticmethod
    def _validate_context(context: InvestigationContext) -> None:
        if not context.investigation_id or not context.fixture_id:
            raise ValueError("Investigation context is incomplete")
        if "\\" in context.source_path:
            raise ValueError("Fixture source path must use repository-relative POSIX separators")
        if not context.source_path.startswith("fixtures/"):
            raise ValueError("Fixture source path is outside the curated fixture root")
        if len(context.report.encode("utf-8")) > 16 * 1024:
            raise ValueError("Bug report exceeds the Stage 1 limit")
        if not re.fullmatch(r"[0-9a-f]{64}", context.source_content_hash):
            raise ValueError("Fixture source digest must be a SHA-256 digest")
        if len(context.source_content.encode("utf-8")) > 64 * 1024:
            raise ValueError("Fixture source content exceeds the provider context limit")