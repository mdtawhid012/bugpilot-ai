from typing import Any

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from fastapi.concurrency import run_in_threadpool

from app.api.dependencies import get_investigation_service
from app.api.request_validation import parse_investigation_request
from app.core.errors import ApplicationError
from app.schemas.investigations import (
    APIErrorResponse,
    CSRFResponse,
    CreateInvestigationResponse,
    EventPageResponse,
    FixtureListResponse,
    InvestigationDetailResponse,
    InvestigationStateResponse,
)
from app.services.investigation_service import InvestigationService


router = APIRouter(prefix="/api/v1")


@router.get("/csrf", response_model=CSRFResponse)
async def get_csrf_token(request: Request, response: Response) -> dict[str, str]:
    response.headers["Cache-Control"] = "no-store"
    return {"token": request.app.state.csrf_token}


@router.get("/fixtures", response_model=FixtureListResponse)
def get_fixtures(request: Request) -> dict[str, list[dict[str, str]]]:
    fixture_service = request.app.state.fixture_service
    return {
        "items": [
            {"id": item.id, "title": item.title, "language": item.language, "revision": item.revision}
            for item in fixture_service.list()
        ]
    }


@router.post(
    "/investigations",
    status_code=202,
    response_model=CreateInvestigationResponse,
    responses={
        400: {"model": APIErrorResponse},
        403: {"model": APIErrorResponse},
        404: {"model": APIErrorResponse},
        413: {"model": APIErrorResponse},
        415: {"model": APIErrorResponse},
        422: {"model": APIErrorResponse},
        500: {"model": APIErrorResponse},
        503: {"model": APIErrorResponse},
    },
)
async def create_investigation(
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    service: InvestigationService = Depends(get_investigation_service),
) -> dict[str, Any]:
    if not idempotency_key:
        raise ApplicationError("invalid_request", "Idempotency-Key is required", 422)
    payload = await parse_investigation_request(request)
    return await run_in_threadpool(service.create, payload.fixture_id, payload.report, idempotency_key)


@router.get("/investigations/{investigation_id}", response_model=InvestigationDetailResponse)
def get_investigation(
    investigation_id: str,
    service: InvestigationService = Depends(get_investigation_service),
) -> dict[str, Any]:
    return service.detail(investigation_id)


@router.get("/investigations/{investigation_id}/events", response_model=EventPageResponse)
def get_investigation_events(
    investigation_id: str,
    request: Request,
    after: int = Query(0, ge=0),
    service: InvestigationService = Depends(get_investigation_service),
) -> dict[str, Any]:
    return service.events(investigation_id, after, request.app.state.settings.event_page_limit)


@router.post(
    "/investigations/{investigation_id}/cancel",
    status_code=202,
    response_model=InvestigationStateResponse,
    responses={
        403: {"model": APIErrorResponse},
        404: {"model": APIErrorResponse},
        409: {"model": APIErrorResponse},
        500: {"model": APIErrorResponse},
    },
)
def cancel_investigation(
    investigation_id: str,
    service: InvestigationService = Depends(get_investigation_service),
) -> dict[str, Any]:
    return service.cancel(investigation_id)


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}