from pydantic import ValidationError

from core.llm_exceptions import (
    LLMEmptyResponseError,
    LLMInvokeError,
    LLMJsonParseError,
    LLMSchemaValidationError,
)
from prompts.novel_prompt import NOVEL_PROMPT_TEMPLATE
from schemas.novel import NovelRequest, NovelResponse
from services.ai.deepseek_client import DeepSeekProvider
from utils.json_parser import parse_json_object


class EventNovelService:
    def __init__(self) -> None:
        self.provider = DeepSeekProvider()

    def generate(self, request: NovelRequest) -> NovelResponse:
        prompt = NOVEL_PROMPT_TEMPLATE.format(
            player_name=request.player_name,
            story_overview=request.novel_summary.story_overview,
            player_journey=request.novel_summary.player_journey,
            final_outcome=request.novel_summary.final_outcome,
        )

        try:
            raw = self.provider.complete_prompt(
                prompt,
                temperature=1.0,
                max_tokens=1200,
            )
        except Exception as e:
            raise LLMInvokeError(f"DeepSeek error: {e}") from e

        if not raw or not raw.strip():
            raise LLMEmptyResponseError("Empty response")

        try:
            data = parse_json_object(raw)
        except Exception as e:
            raise LLMJsonParseError(f"JSON parse error: {e}") from e

        try:
            return NovelResponse.model_validate(data)
        except ValidationError as e:
            raise LLMSchemaValidationError(f"Schema error: {e}") from e