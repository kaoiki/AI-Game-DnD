from fastapi import APIRouter

from core.response import error, success
from events.dispatcher import EventDispatcher
from events.handlers.init_handler import InitEventHandler
from events.types import EventType
from schemas.base import ApiResponse
from schemas.invoke import InvokeRequest

router = APIRouter()

dispatcher = EventDispatcher()
dispatcher.register(EventType.INIT, InitEventHandler())


@router.post("/invoke", response_model=ApiResponse)
def invoke(request: InvokeRequest) -> ApiResponse:
    try:
        result = dispatcher.dispatch(request)
        return success(data=result)
    except ValueError as exc:
        return error(message=str(exc), code=1)
    except Exception as exc:
        return error(message=f"Invoke failed: {exc}", code=1)