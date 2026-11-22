import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.core.errors import ConflictError, NotFoundError
from app.models.evidence import ContentType, EvidenceKind, EvidenceRecord, ProducerKind
from app.models.investigation import InvalidStateTransition, InvestigationStatus, require_transition
from app.repositories.database import Database
from app.repositories.investigation_repository import InvestigationRepository


class InvestigationRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.repository = InvestigationRepository(Database(Path(self.temporary_directory.name)))
        self.repository.database.initialize()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _create(self, investigation_id: str = "investigation-1") -> dict:
        return self.repository.create(
            investigation_id,
            "discount-calculator",
            "The discount is incorrect",
            f"key-{investigation_id}",
            f"hash-{investigation_id}",
        )

    def test_create_persists_report_initial_event_and_idempotency(self) -> None:
        created = self._create()
        detail = self.repository.get_detail(created["id"])

        self.assertEqual(detail["report"], "The discount is incorrect")
        self.assertEqual(detail["status"], InvestigationStatus.QUEUED.value)
        self.assertEqual(detail["latest_event_sequence"], 1)
        self.assertEqual(self.repository.get_events(created["id"], 0, 10)["items"][0]["sequence"], 1)
        self.assertEqual(self.repository.get_idempotency("key-investigation-1")["investigation_id"], created["id"])

    def test_completion_atomically_persists_provenance_and_terminal_event(self) -> None:
        created = self._create()
        self.repository.start_analysis(created["id"])
        evidence = EvidenceRecord(
            id="evidence-1",
            kind=EvidenceKind.HYPOTHESIS,
            content_type=ContentType.GENERATED,
            producer_kind=ProducerKind.FAKE_PROVIDER,
            producer_version="fixture-fake-v1",
            source_fixture_id="discount-calculator",
            title="Hypothesis",
            summary="Synthetic proposal",
        )

        self.assertTrue(self.repository.complete(created["id"], [evidence]))
        detail = self.repository.get_detail(created["id"])
        events = self.repository.get_events(created["id"], 0, 10)["items"]
        self.assertEqual(detail["status"], InvestigationStatus.REVIEWABLE.value)
        self.assertEqual(detail["evidence"][0]["producer_kind"], ProducerKind.FAKE_PROVIDER.value)
        self.assertEqual([item["sequence"] for item in events], [1, 2, 3, 4])
        self.assertTrue(all(item["sequence"] > 1 for item in self.repository.get_events(created["id"], 1, 10)["items"]))

    def test_restart_recovery_marks_queued_rows_interrupted(self) -> None:
        created = self._create()

        self.assertEqual(self.repository.recover_unfinished(), 1)
        detail = self.repository.get_detail(created["id"])
        events = self.repository.get_events(created["id"], 1, 10)["items"]
        self.assertEqual(detail["status"], InvestigationStatus.INTERRUPTED.value)
        self.assertEqual(events[-1]["type"], "investigation_interrupted")

    def test_cancel_is_idempotent_and_terminal_completion_conflicts(self) -> None:
        created = self._create()
        first = self.repository.cancel(created["id"])
        second = self.repository.cancel(created["id"])

        self.assertEqual(first["status"], InvestigationStatus.CANCELLED.value)
        self.assertEqual(second["latest_event_sequence"], first["latest_event_sequence"])
        self.assertFalse(self.repository.start_analysis(created["id"]))

    def test_every_documented_transition_is_accepted_and_others_are_rejected(self) -> None:
        valid = {
            InvestigationStatus.QUEUED: {
                InvestigationStatus.ANALYZING,
                InvestigationStatus.CANCELLED,
                InvestigationStatus.INTERRUPTED,
            },
            InvestigationStatus.ANALYZING: {
                InvestigationStatus.REVIEWABLE,
                InvestigationStatus.FAILED,
                InvestigationStatus.CANCELLED,
                InvestigationStatus.INTERRUPTED,
            },
        }
        for current in InvestigationStatus:
            for requested in InvestigationStatus:
                with self.subTest(current=current, requested=requested):
                    if requested in valid.get(current, set()):
                        require_transition(current, requested)
                    else:
                        with self.assertRaises(InvalidStateTransition):
                            require_transition(current, requested)

    def test_initial_investigation_event_failure_rolls_back_every_row(self) -> None:
        connection = self.repository.database.connect()
        try:
            connection.execute(
                """CREATE TRIGGER reject_initial_event BEFORE INSERT ON investigation_events
                   WHEN NEW.sequence = 1 BEGIN SELECT RAISE(ABORT, 'test failure'); END"""
            )
        finally:
            connection.close()

        with self.assertRaises(sqlite3.IntegrityError):
            self._create()
        self.assertIsNone(self.repository.get_idempotency("key-investigation-1"))
        with self.assertRaises(NotFoundError):
            self.repository.get_detail("investigation-1")

    def test_cancel_and_completion_race_has_one_atomic_terminal_winner(self) -> None:
        created = self._create()
        self.repository.start_analysis(created["id"])
        barrier = threading.Barrier(2)
        evidence = EvidenceRecord(
            id="race-evidence",
            kind=EvidenceKind.HYPOTHESIS,
            content_type=ContentType.GENERATED,
            producer_kind=ProducerKind.FAKE_PROVIDER,
            producer_version="fixture-fake-v1",
            source_fixture_id="discount-calculator",
            title="Hypothesis",
            summary="Synthetic proposal",
        )

        def cancel():
            barrier.wait()
            try:
                return self.repository.cancel(created["id"])["status"]
            except ConflictError:
                return "conflict"

        def complete():
            barrier.wait()
            try:
                return "completed" if self.repository.complete(created["id"], [evidence]) else "discarded"
            except ConflictError:
                return "conflict"

        with ThreadPoolExecutor(max_workers=2) as executor:
            cancel_result = executor.submit(cancel)
            complete_result = executor.submit(complete)
            cancel_outcome = cancel_result.result()
            complete_outcome = complete_result.result()

        detail = self.repository.get_detail(created["id"])
        events = self.repository.get_events(created["id"], 0, 20)["items"]
        sequences = [event["sequence"] for event in events]
        self.assertEqual(sequences, list(range(1, len(sequences) + 1)))
        if detail["status"] == InvestigationStatus.CANCELLED.value:
            self.assertIn(complete_outcome, {"discarded", "conflict"})
            self.assertEqual(detail["evidence"], [])
        else:
            self.assertEqual(detail["status"], InvestigationStatus.REVIEWABLE.value)
            self.assertEqual(cancel_outcome, "conflict")
            self.assertEqual([item["id"] for item in detail["evidence"]], ["race-evidence"])
