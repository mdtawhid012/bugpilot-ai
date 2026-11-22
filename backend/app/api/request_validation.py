import json

from fastapi import Request
from pydantic import ValidationError

from app.core.errors import ApplicationError
from app.schemas.investigations import InvestigationCreateRequest


MAX_JSON_BODY_BYTES = 32 * 1024
MAX_REPORT_BYTES = 16 * 1024


async def parse_investigation_request(request: Request) -> InvestigationCreateRequest:
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type != "application/json":
        raise ApplicationError("invalid_request", "Content-Type must be application/json", 415)
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) > MAX_JSON_BODY_BYTES:
                raise ApplicationError("invalid_request", "Request body exceeds the allowed size", 413)
        except ValueError as error:
            raise ApplicationError("invalid_request", "Content-Length is invalid", 400) from error
    chunks = bytearray()
    async for chunk in request.stream():
        chunks.extend(chunk)
        if len(chunks) > MAX_JSON_BODY_BYTES:
            raise ApplicationError("invalid_request", "Request body exceeds the allowed size", 413)
    try:
        payload = InvestigationCreateRequest.model_validate(json.loads(chunks))
    except (json.JSONDecodeError, UnicodeDecodeError, ValidationError, TypeError) as error:
        raise ApplicationError("invalid_request", "Request body does not match the expected schema", 422) from error
    if len(payload.report.encode("utf-8")) > MAX_REPORT_BYTES:
        raise ApplicationError("invalid_request", "Report exceeds the 16 KiB UTF-8 limit", 422)
    return payload