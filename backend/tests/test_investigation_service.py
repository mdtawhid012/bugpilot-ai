import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.core.errors import CapacityExhaustedError, ConflictError
from app.integrations.ai.fake_provider import FakeProvider
from app.integrations.ai.protocols import InvestigationContext
from app.integrations.execution.simulated_runner import SimulatedRunner
from app.models.evidence import EvidenceRecord
from app.repositories.database import Database
from app.repositories.investigation_repository import InvestigationRepository
from app.services.fixture_service import Fixture, FixtureService
from app.services.investigation_service import InvestigationService
from app.workers.coordinator import Coordinator
from app.workers.investigation_worker import InvestigationWorker


class InvestigationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.repository = InvestigationRepository(Database(Path(self.temporary_directory.name)))
        self.repository.database.initialize()
        worker = InvestigationWorker(self.repository, FakeProvider(), SimulatedRunner(), FixtureService(()))
        self.coordinator = Coordinator(1, worker, self.repository)
        fixtures = FixtureService((Fixture("fixture-a", "Fixture A", "python", "test-revision"),))
        self.service = InvestigationService(self.repository, fixtures, self.coordinator)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_saturated_admission_does_not_create_row_or_consume_key(self) -> None:
        held_reservation = self.coordinator.reserve()
        try:
            with self.assertRaises(CapacityExhaustedError):
                self.service.create("fixture-a", "A report", "unused-key")
            self.assertIsNone(self.repository.get_idempotency("unused-key"))
        finally:
            held_reservation.release()

    def test_idempotent_replay_works_while_full_and_conflicts_on_changed_body(self) -> None:
        created = self.service.create("fixture-a", "A report", "same-key")
        self.repository.start_analysis(created["id"])
        self.repository.complete(created["id"], [])

        replay = self.service.create("fixture-a", "A report", "same-key")
        self.assertEqual(replay["id"], created["id"])
        self.assertEqual(replay["status"], "reviewable")
        with self.assertRaises(ConflictError):
            self.service.create("fixture-a", "Different report", "same-key")
        with self.assertRaises(CapacityExhaustedError):
            self.service.create("fixture-a", "Another report", "new-key")
        self.assertIsNone(self.repository.get_idempotency("new-key"))

    def test_concurrent_same_key_requests_resolve_to_one_investigation(self) -> None:
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(
                executor.map(
                    lambda _: self.service.create("fixture-a", "Same report", "concurrent-key"),
                    range(8),
                )
            )

        self.assertEqual(len({result["id"] for result in results}), 1)
        self.assertEqual(self.repository.get_idempotency("concurrent-key")["investigation_id"], results[0]["id"])

    def test_failed_sqlite_creation_releases_reserved_capacity_and_key(self) -> None:
        connection = self.repository.database.connect()
        try:
            connection.execute(
                """CREATE TRIGGER reject_investigation BEFORE INSERT ON investigations
                   BEGIN SELECT RAISE(ABORT, 'test failure'); END"""
            )
        finally:
            connection.close()

        with self.assertRaises(sqlite3.IntegrityError):
            self.service.create("fixture-a", "A report", "retryable-key")
        self.assertIsNone(self.repository.get_idempotency("retryable-key"))
        connection = self.repository.database.connect()
        try:
            connection.execute("DROP TRIGGER reject_investigation")
        finally:
            connection.close()

        created = self.service.create("fixture-a", "A report", "retryable-key")
        self.assertEqual(created["status"], "queued")

    def test_worker_discards_late_provider_result_after_cancellation(self) -> None:
        source_ref = {
            "path": "fixtures/discount_calculator/calculator.py",
            "line_start": 1,
            "line_end": 2,
            "revision": "synthetic-v1",
            "content_hash": "9c8b2223223dce44fe1e8f7c526f19f34051e559f69a63f21e894eba11999824",
        }
        created = self.repository.create(
            "worker-cancel-race",
            "discount-calculator",
            "A report",
            "worker-cancel-key",
            "worker-cancel-hash",
        )
        provider_entered = threading.Event()
        release_provider = threading.Event()

        class BlockingProvider:
            def generate(self, context: InvestigationContext) -> list[EvidenceRecord]:
                provider_entered.set()
                if not release_provider.wait(timeout=5):
                    raise TimeoutError("Test did not release fake provider")
                return []

        class RecordingExecution:
            called = False

            def result(self, investigation_id: str, fixture_id: str) -> EvidenceRecord:
                self.called = True
                return SimulatedRunner().result(investigation_id, fixture_id)

        execution = RecordingExecution()
        fixture_service = FixtureService(
            (Fixture("discount-calculator", "Discount calculator", "python", "synthetic-v1", source_ref),)
        )
        worker = InvestigationWorker(self.repository, BlockingProvider(), execution, fixture_service)
        worker_thread = threading.Thread(target=worker.process, args=(created["id"],))
        worker_thread.start()
        self.assertTrue(provider_entered.wait(timeout=5))
        self.repository.cancel(created["id"])
        release_provider.set()
        worker_thread.join(timeout=5)

        self.assertFalse(worker_thread.is_alive())
        self.assertFalse(execution.called)
        detail = self.repository.get_detail(created["id"])
        self.assertEqual(detail["status"], "cancelled")
        self.assertEqual(detail["evidence"], [])

    def test_provider_failure_transitions_investigation_to_failed(self) -> None:
        source_ref = {
            "path": "fixtures/discount_calculator/calculator.py",
            "line_start": 1,
            "line_end": 2,
            "revision": "synthetic-v1",
            "content_hash": "9c8b2223223dce44fe1e8f7c526f19f34051e559f69a63f21e894eba11999824",
        }
        fixture_service = FixtureService(
            (Fixture("discount-calculator", "Discount calculator", "python", "synthetic-v1", source_ref),)
        )

        class FailingProvider:
            def generate(self, context: InvestigationContext) -> list[EvidenceRecord]:
                raise ValueError("deterministic provider failure")

        created = self.repository.create(
            "provider-failure",
            "discount-calculator",
            "The discount result is wrong.",
            "provider-failure-key",
            "provider-failure-hash",
        )
        worker = InvestigationWorker(
            self.repository,
            FailingProvider(),
            SimulatedRunner(),
            fixture_service,
        )

        try:
            worker.process(created["id"])
        except ValueError:
            self.repository.fail(created["id"])

        detail = self.repository.get_detail(created["id"])
        self.assertEqual(detail["status"], "failed")
        self.assertEqual(detail["evidence"], [])

    def test_real_fixture_context_produces_generated_and_simulated_evidence(self) -> None:
        source_ref = {
            "path": "fixtures/discount_calculator/calculator.py",
            "line_start": 1,
            "line_end": 2,
            "revision": "synthetic-v1",
            "content_hash": "9c8b2223223dce44fe1e8f7c526f19f34051e559f69a63f21e894eba11999824",
        }
        fixture_service = FixtureService(
            (Fixture("discount-calculator", "Discount calculator", "python", "synthetic-v1", source_ref),)
        )
        worker = InvestigationWorker(
            self.repository,
            FakeProvider(),
            SimulatedRunner(),
            fixture_service,
        )
        created = self.repository.create(
            "intelligence-engine",
            "discount-calculator",
            "The discount result is wrong.",
            "intelligence-key",
            "intelligence-hash",
        )

        worker.process(created["id"])
        detail = self.repository.get_detail(created["id"])
        kinds = [item["kind"] for item in detail["evidence"]]
        producers = [item["producer_kind"] for item in detail["evidence"]]

        self.assertEqual(detail["status"], "reviewable")
        self.assertEqual(detail["execution_status"], "simulated")
        self.assertEqual(detail["verification_outcome"], "not_run")
        self.assertEqual(kinds, ["source_reference", "hypothesis", "test_proposal", "patch_proposal", "execution_result"])
        self.assertIn("fake_provider", producers)
        self.assertIn("simulated_runner", producers)
        self.assertNotIn("verified_patch", [item["summary"] for item in detail["evidence"]])