from typing import Any

from pydantic import BaseModel, ConfigDict, StrictStr


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class InvestigationCreateRequest(StrictSchema):
    fixture_id: StrictStr
    report: StrictStr


class APIErrorResponse(StrictSchema):
    code: str
    message: str
    request_id: str


class CSRFResponse(StrictSchema):
    token: str


class FixtureItem(StrictSchema):
    id: str
    title: str
    language: str
    revision: str


class FixtureListResponse(StrictSchema):
    items: list[FixtureItem]


class CreateInvestigationResponse(StrictSchema):
    id: str
    status: str
    verification_outcome: str
    execution_status: str
    provider_mode: str


class InvestigationStateResponse(StrictSchema):
    id: str
    status: str
    verification_outcome: str
    execution_status: str
    created_at: str
    updated_at: str
    latest_event_sequence: int


class FixtureReference(StrictSchema):
    id: str
    title: str
    revision: str


class SourceReference(StrictSchema):
    path: str
    line_start: int
    line_end: int
    revision: str
    content_hash: str


class EvidenceItem(StrictSchema):
    id: str
    kind: str
    content_type: str
    producer_kind: str
    producer_version: str
    source_fixture_id: str | None = None
    title: str
    summary: str
    source_ref: SourceReference | None = None


class InvestigationDetailResponse(StrictSchema):
    id: str
    status: str
    report: str
    verification_outcome: str
    execution_status: str
    fixture: FixtureReference
    created_at: str
    updated_at: str
    latest_event_sequence: int
    evidence: list[EvidenceItem]


class InvestigationEvent(StrictSchema):
    sequence: int
    type: str
    created_at: str
    data: dict[str, Any]


class EventPageResponse(StrictSchema):
    items: list[InvestigationEvent]
    next_cursor: int | None