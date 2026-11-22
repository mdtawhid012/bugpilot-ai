from fastapi import Request

from app.services.investigation_service import InvestigationService


def get_investigation_service(request: Request) -> InvestigationService:
    return request.app.state.investigation_service