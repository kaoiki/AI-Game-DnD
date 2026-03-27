# from pydantic import ValidationError

# from core.llm_exceptions import (
#     LLMEmptyResponseError,
#     LLMInvokeError,
#     LLMJsonParseError,
#     LLMSchemaValidationError,
# )
# from prompts.event_init_prompt import DND_EVENT_INIT_PROMPT
# from schemas.event_init import DndEventInitResponse
# from services.ai.deepseek_client import DeepSeekProvider
# from utils.json_parser import parse_json_object


# class EventInitService:
#     def __init__(self) -> None:
#         self.provider = DeepSeekProvider()

#     def init_dnd_event(self) -> DndEventInitResponse:
#         try:
#             raw_text = self.provider.complete_prompt(
#                 DND_EVENT_INIT_PROMPT,
#                 temperature=1.3,
#                 max_tokens=180,
#             )
#         except Exception as exc:
#             raise LLMInvokeError(f"DeepSeek invoke failed: {exc}") from exc

#         if not raw_text or not raw_text.strip():
#             raise LLMEmptyResponseError("DeepSeek returned empty content")

#         try:
#             data = parse_json_object(raw_text)
#         except Exception as exc:
#             raise LLMJsonParseError(f"Failed to parse model JSON: {exc}") from exc

#         try:
#             return DndEventInitResponse.model_validate(data)
#         except ValidationError as exc:
#             raise LLMSchemaValidationError(
#                 f"DndEventInitResponse validation failed: {exc}"
#             ) from exc

import random

from pydantic import ValidationError

from core.config import settings
from core.llm_exceptions import (
    LLMEmptyResponseError,
    LLMInvokeError,
    LLMJsonParseError,
    LLMSchemaValidationError,
)
from prompts.event_init_prompt import build_dnd_event_init_prompt
from schemas.event_init import DndEventInitResponse, DndEventInitSlots
from services.ai.deepseek_client import DeepSeekProvider
from utils.json_parser import parse_json_object


class EventInitService:
    def __init__(self) -> None:
        self.provider = DeepSeekProvider()

    def init_dnd_event(self) -> DndEventInitResponse:
        event_pool = settings.event_init_random_events
        if not event_pool:
            raise ValueError("EVENT_INIT_RANDOM_EVENTS is empty")

        target_event = random.choice(event_pool)
        prompt = build_dnd_event_init_prompt(target_event)

        try:
            raw_text = self.provider.complete_prompt(
                prompt,
                temperature=1.3,
                max_tokens=180,
            )
        except Exception as exc:
            raise LLMInvokeError(f"DeepSeek invoke failed: {exc}") from exc

        if not raw_text or not raw_text.strip():
            raise LLMEmptyResponseError("DeepSeek returned empty content")

        try:
            data = parse_json_object(raw_text)
        except Exception as exc:
            raise LLMJsonParseError(f"Failed to parse model JSON: {exc}") from exc

        try:
            slots = DndEventInitSlots.model_validate(data)
        except ValidationError as exc:
            raise LLMSchemaValidationError(
                f"DndEventInitSlots validation failed: {exc}"
            ) from exc

        return DndEventInitResponse(
            event=target_event,
            slots=slots,
        )