from fastapi import APIRouter

from core.response import error, success
from events.dispatcher import EventDispatcher
from events.handlers.init_handler import InitEventHandler
from events.handlers.decision_handler import DecisionEventHandler
from events.handlers.combat_handler import CombatEventHandler
from events.handlers.puzzle_handler import PuzzleEventHandler
from events.handlers.end_handler import EndEventHandler
from events.types import EventType
from schemas.base import ApiResponse
from schemas.invoke import InvokeRequest

router = APIRouter()

dispatcher = EventDispatcher()
dispatcher.register(EventType.INIT, InitEventHandler())
dispatcher.register(EventType.DECISION, DecisionEventHandler())
dispatcher.register(EventType.COMBAT, CombatEventHandler())
dispatcher.register(EventType.PUZZLE, PuzzleEventHandler())
dispatcher.register(EventType.END, EndEventHandler())



@router.post("/invoke", response_model=ApiResponse)
def invoke(request: InvokeRequest) -> ApiResponse:
    try:
        result = dispatcher.dispatch(request)
        return success(data=result)
    except ValueError as exc:
        return error(message=str(exc), code=1)
    except Exception as exc:
        return error(message=f"Invoke failed: {exc}", code=1)