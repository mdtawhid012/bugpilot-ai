import logging
import queue
import threading
from dataclasses import dataclass

from app.core.errors import CapacityExhaustedError
from app.repositories.investigation_repository import InvestigationRepository
from app.workers.investigation_worker import InvestigationWorker


logger = logging.getLogger(__name__)


@dataclass
class CapacityReservation:
    coordinator: "Coordinator"
    active: bool = True

    def release(self) -> None:
        if self.active:
            self.active = False
            self.coordinator._capacity.release()

    def enqueue(self, investigation_id: str) -> None:
        if not self.active:
            raise RuntimeError("Coordinator capacity reservation is no longer active")
        try:
            self.coordinator._queue.put_nowait(investigation_id)
        except queue.Full as error:
            self.release()
            raise RuntimeError("Reserved coordinator capacity was unavailable") from error
        self.active = False


class Coordinator:
    def __init__(self, capacity: int, worker: InvestigationWorker, repository: InvestigationRepository) -> None:
        self._queue: queue.Queue[str | None] = queue.Queue(maxsize=capacity)
        self._capacity = threading.BoundedSemaphore(capacity)
        self._worker = worker
        self._repository = repository
        self._thread: threading.Thread | None = None

    def reserve(self) -> CapacityReservation:
        if not self._capacity.acquire(blocking=False):
            raise CapacityExhaustedError()
        return CapacityReservation(self)

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, name="bugpilot-coordinator", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._thread is None:
            return
        self._queue.put(None)
        self._thread.join()
        self._thread = None

    def _run(self) -> None:
        while True:
            investigation_id = self._queue.get()
            if investigation_id is None:
                self._queue.task_done()
                return
            self._capacity.release()
            try:
                self._worker.process(investigation_id)
            except Exception as error:
                logger.error(
                    "Investigation worker failed",
                    extra={"investigation_id": investigation_id, "exception_type": type(error).__name__},
                )
                try:
                    self._repository.fail(investigation_id)
                except Exception as transition_error:
                    logger.error(
                        "Could not persist investigation failure",
                        extra={"investigation_id": investigation_id, "exception_type": type(transition_error).__name__},
                    )
            finally:
                self._queue.task_done()