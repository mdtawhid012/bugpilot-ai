import hashlib
import json
import threading
import uuid
from typing import Any, Protocol

from app.core.errors import ApplicationError, ConflictError
from app.repositories.investigation_repository import InvestigationRepository
from app.services.fixture_service import FixtureService


class CoordinatorReservation(Protocol):
    def enqueue(self, investigation_id: str) -> None: ...

    def release(self) -> None: ...


class CoordinatorPort(Protocol):
    def reserve(self) -> CoordinatorReservation: ...


class InvestigationService:
    def __init__(
        self,
        repository: InvestigationRepository,
        fixtures: FixtureService,
        coordinator: CoordinatorPort,
    ) -> None:
        self.repository = repository
        self.fixtures = fixtures
        self.coordinator = coordinator
        self._create_lock = threading.Lock()

    def create(self, fixture_id: str, report: str, idempotency_key: str) -> dict[str, Any]:
        request_hash = self._request_hash(fixture_id, report)
        with self._create_lock:
            existing = self.repository.get_idempotency(idempotency_key)
            if existing is not None:
                return self._replay(existing["request_hash"], request_hash, existing["investigation_id"])
            self.fixtures.get(fixture_id)
            reservation = self.coordinator.reserve()
            try:
                existing = self.repository.get_idempotency(idempotency_key)
                if existing is not None:
                    return self._replay(existing["request_hash"], request_hash, existing["investigation_id"])
                investigation_id = str(uuid.uuid4())
                response = self.repository.create(
                    investigation_id,
                    fixture_id,
                    report,
                    idempotency_key,
                    request_hash,
                )
                try:
                    reservation.enqueue(investigation_id)
                except Exception as error:
                    self.repository.interrupt_enqueue_failure(investigation_id)
                    raise ApplicationError("internal_error", "The investigation could not be scheduled", 500) from error
                response["provider_mode"] = "fake"
                return response
            finally:
                reservation.release()

    def detail(self, investigation_id: str) -> dict[str, Any]:
        detail = self.repository.get_detail(investigation_id)
        fixture = self.fixtures.get(detail.pop("fixture_id"))
        detail["fixture"] = {"id": fixture.id, "title": fixture.title, "revision": fixture.revision}
        return detail

    def events(self, investigation_id: str, after: int, limit: int) -> dict[str, Any]:
        return self.repository.get_events(investigation_id, after, limit)

    def cancel(self, investigation_id: str) -> dict[str, Any]:
        return self.repository.cancel(investigation_id)

    @staticmethod
    def _request_hash(fixture_id: str, report: str) -> str:
        payload = json.dumps(
            {"fixture_id": fixture_id, "report": report},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _replay(self, stored_hash: str, request_hash: str, investigation_id: str) -> dict[str, Any]:
        if stored_hash != request_hash:
            raise ConflictError("idempotency_conflict", "The idempotency key was already used for a different request")
        summary = self.repository.get_summary(investigation_id)
        return {
            "id": summary["id"],
            "status": summary["status"],
            "verification_outcome": summary["verification_outcome"],
            "execution_status": summary["execution_status"],
            "provider_mode": "fake",
        }