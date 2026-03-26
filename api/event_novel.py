from fastapi import APIRouter

from core.response import error, success
from schemas.base import ApiResponse
from schemas.novel import NovelRequest
from services.event_novel_service import EventNovelService

router = APIRouter(tags=["novel"])

service = EventNovelService()


@router.post("/novel", response_model=ApiResponse)
def novel(request: NovelRequest) -> ApiResponse:
    try:
        result = service.generate(request)
        return success(data=result.model_dump())
    except ValueError as e:
        return error(message=str(e), code=1)
    except Exception as e:
        return error(message=f"novel failed: {e}", code=1)