import uuid
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from app.core.config import Settings
from app.core.security import csrf_token_matches


def install_local_security_middleware(app: FastAPI, settings: Settings) -> None:
    @app.middleware("http")
    async def enforce_local_request_boundary(request: Request, call_next: Any) -> Response:
        request.state.request_id = str(uuid.uuid4())
        if request.headers.get("host", "") not in settings.allowed_hosts:
            return _error(request, "invalid_request", "Invalid request host", 400)
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            if request.headers.get("origin") != settings.ui_origin:
                return _error(request, "invalid_request", "Request origin is not allowed", 403)
            if request.headers.get("sec-fetch-site") != "same-origin":
                return _error(request, "invalid_request", "Request site is not allowed", 403)
            if not csrf_token_matches(
                getattr(app.state, "csrf_token", ""),
                request.headers.get("x-csrf-token", ""),
            ):
                return _error(request, "invalid_request", "CSRF token is invalid", 403)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response


def _error(request: Request, code: str, message: str, status_code: int) -> JSONResponse:
    request_id = request.state.request_id
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "message": message, "request_id": request_id},
        headers={"X-Request-ID": request_id},
    )