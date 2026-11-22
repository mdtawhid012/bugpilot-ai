from enum import Enum


class InvestigationStatus(str, Enum):
    QUEUED = "queued"
    ANALYZING = "analyzing"
    REVIEWABLE = "reviewable"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"


class EventType(str, Enum):
    QUEUED = "investigation_queued"
    ANALYSIS_STARTED = "analysis_started"
    EVIDENCE_ADDED = "evidence_added"
    REVIEWABLE = "investigation_reviewable"
    FAILED = "investigation_failed"
    CANCELLED = "investigation_cancelled"
    INTERRUPTED = "investigation_interrupted"


class ExecutionStatus(str, Enum):
    NOT_REQUESTED = "not_requested"
    SIMULATED = "simulated"


class VerificationOutcome(str, Enum):
    NOT_RUN = "not_run"


class InvalidStateTransition(Exception):
    def __init__(self, current: InvestigationStatus, requested: InvestigationStatus) -> None:
        self.current = current
        self.requested = requested
        super().__init__(f"Cannot transition from {current.value} to {requested.value}")


_ALLOWED_TRANSITIONS = {
    InvestigationStatus.QUEUED: frozenset(
        {InvestigationStatus.ANALYZING, InvestigationStatus.CANCELLED, InvestigationStatus.INTERRUPTED}
    ),
    InvestigationStatus.ANALYZING: frozenset(
        {
            InvestigationStatus.REVIEWABLE,
            InvestigationStatus.FAILED,
            InvestigationStatus.CANCELLED,
            InvestigationStatus.INTERRUPTED,
        }
    ),
}


def require_transition(current: InvestigationStatus, requested: InvestigationStatus) -> None:
    if requested not in _ALLOWED_TRANSITIONS.get(current, frozenset()):
        raise InvalidStateTransition(current, requested)