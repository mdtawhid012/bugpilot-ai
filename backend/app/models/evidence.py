from dataclasses import dataclass
from enum import Enum
from typing import Any


class EvidenceKind(str, Enum):
    SOURCE_REFERENCE = "source_reference"
    HYPOTHESIS = "hypothesis"
    TEST_PROPOSAL = "test_proposal"
    PATCH_PROPOSAL = "patch_proposal"
    EXECUTION_RESULT = "execution_result"


class ContentType(str, Enum):
    GENERATED = "generated"
    OBSERVED = "observed"
    SIMULATED = "simulated"


class ProducerKind(str, Enum):
    FIXTURE = "fixture"
    FAKE_PROVIDER = "fake_provider"
    SIMULATED_RUNNER = "simulated_runner"


@dataclass(frozen=True)
class EvidenceRecord:
    id: str
    kind: EvidenceKind
    content_type: ContentType
    producer_kind: ProducerKind
    producer_version: str
    source_fixture_id: str | None
    title: str
    summary: str
    source_ref: dict[str, Any] | None = None