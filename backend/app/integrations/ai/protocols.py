from dataclasses import dataclass
from typing import Protocol

from app.models.evidence import EvidenceRecord


@dataclass(frozen=True)
class InvestigationContext:
    investigation_id: str
    report: str
    fixture_id: str
    fixture_title: str
    fixture_language: str
    fixture_revision: str
    source_path: str
    source_content: str
    source_line_start: int
    source_line_end: int
    source_revision: str
    source_content_hash: str


class ProposalProvider(Protocol):
    def generate(self, context: InvestigationContext) -> list[EvidenceRecord]: ...