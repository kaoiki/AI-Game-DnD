from fastapi import APIRouter

from core.response import error, success
from schemas.base import ApiResponse
from services.event_init_service import EventInitService

router = APIRouter(prefix="/event-init", tags=["event-init"])

service = EventInitService()


@router.post("/init", response_model=ApiResponse)
def init_dnd_event() -> ApiResponse:
    try:
        result = service.init_dnd_event()
        return success(data=result.model_dump())
    except ValueError as exc:
        return error(message=str(exc), code=1)
    except Exception as exc:
        return error(message=f"Event init failed: {exc}", code=1)