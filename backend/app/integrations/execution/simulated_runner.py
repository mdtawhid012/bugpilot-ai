import hashlib
import uuid

from app.models.evidence import ContentType, EvidenceKind, EvidenceRecord, ProducerKind


class SimulatedRunner:
    version = "simulated-runner-v1"

    def result(self, investigation_id: str, fixture_id: str) -> EvidenceRecord:
        seed = f"{self.version}|{investigation_id}|{fixture_id}|execution_result"
        evidence_id = str(uuid.UUID(bytes=hashlib.sha256(seed.encode("utf-8")).digest()[:16], version=5))
        return EvidenceRecord(
            id=evidence_id,
            kind=EvidenceKind.EXECUTION_RESULT,
            content_type=ContentType.SIMULATED,
            producer_kind=ProducerKind.SIMULATED_RUNNER,
            producer_version=self.version,
            source_fixture_id=fixture_id,
            title="Execution not performed",
            summary="This is a simulated result. No target code or test suite was executed.",
        )