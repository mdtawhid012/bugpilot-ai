import logging
import secrets
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.middleware import install_local_security_middleware
from app.api.router import router
from app.core.config import Settings
from app.core.errors import ApplicationError
from app.core.logging import log_internal_failure
from app.integrations.ai.fake_provider import FakeProvider
from app.integrations.execution.simulated_runner import SimulatedRunner
from app.repositories.database import Database
from app.repositories.investigation_repository import InvestigationRepository
from app.services.fixture_service import Fixture, FixtureService
from app.services.investigation_service import InvestigationService
from app.workers.coordinator import Coordinator
from app.workers.investigation_worker import InvestigationWorker


logger = logging.getLogger(__name__)
DEFAULT_FIXTURES = (
    Fixture(
        "discount-calculator",
        "Discount calculator",
        "python",
        "synthetic-v1",
        {
            "path": "fixtures/discount_calculator/calculator.py",
            "line_start": 1,
            "line_end": 2,
            "revision": "synthetic-v1",
            "content_hash": "9c8b2223223dce44fe1e8f7c526f19f34051e559f69a63f21e894eba11999824",
        },
    ),
)


def create_app(settings: Settings | None = None, fixtures: tuple[Fixture, ...] = DEFAULT_FIXTURES) -> FastAPI:
    settings = settings or Settings.from_environment()
    settings.validate()
    database = Database(settings.data_directory)
    repository = InvestigationRepository(database)
    fixture_service = FixtureService(fixtures)
    worker = InvestigationWorker(repository, FakeProvider(), SimulatedRunner(), fixture_service)
    coordinator = Coordinator(settings.coordinator_capacity, worker, repository)
    investigation_service = InvestigationService(repository, fixture_service, coordinator)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        database.initialize()
        repository.recover_unfinished()
        app.state.investigation_service = investigation_service
        app.state.fixture_service = fixture_service
        app.state.csrf_token = secrets.token_urlsafe(32)
        coordinator.start()
        try:
            yield
        finally:
            coordinator.stop()

    app = FastAPI(title="BugPilot AI local API", version="1", lifespan=lifespan)
    app.state.settings = settings
    install_local_security_middleware(app, settings)
    app.include_router(router)

    @app.exception_handler(ApplicationError)
    async def application_error_handler(request: Request, error: ApplicationError) -> JSONResponse:
        return _error_response(request, error.code, error.message, error.status_code)

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(request: Request, error: RequestValidationError) -> JSONResponse:
        return _error_response(request, "invalid_request", "Request validation failed", 422)

    @app.exception_handler(HTTPException)
    async def http_error_handler(request: Request, error: HTTPException) -> JSONResponse:
        if error.status_code == 404:
            return _error_response(request, "not_found", "Resource not found", 404)
        return _error_response(request, "invalid_request", "Request could not be completed", error.status_code)

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, error: Exception) -> JSONResponse:
        log_internal_failure(logger, "Unhandled API error", getattr(request.state, "request_id", ""), error)
        return _error_response(request, "internal_error", "An internal error occurred", 500)

    return app


def _error_response(request: Request, code: str, message: str, status_code: int) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "message": message, "request_id": request_id},
        headers={"X-Request-ID": request_id},
    )