from typing import Protocol

from app.models.evidence import EvidenceRecord


class ExecutionAdapter(Protocol):
    def result(self, investigation_id: str, fixture_id: str) -> EvidenceRecord: ...