from pydantic import ValidationError

from core.llm_exceptions import (
    LLMEmptyResponseError,
    LLMInvokeError,
    LLMJsonParseError,
    LLMSchemaValidationError,
)
from events.base import BaseEventHandler
from prompts.init_prompt import render_init_prompt
from repositories.memory_state_repository import MemoryStateRepository
from schemas.init import InitRequest, InitResponse, InitTime
from schemas.invoke import InvokeRequest, InvokeResponseData
from services.ai.deepseek_client import DeepSeekProvider
from utils.json_parser import parse_json_object


class InitEventHandler(BaseEventHandler):
    """
    INIT 事件处理器。

    Step 8：
    - 保持真实 INIT 链路不变
    - 在成功返回后保存最小状态快照
    - 为后续 LOOP 事件做准备

    当前保存内容：
    - session_id
    - event_type
    - ai_state
    - last_output

    db9.ai 预留：
    - 当前仍通过 _build_augmented_context() 预留增强上下文入口
    - 未来可在 Prompt 前读取 db9.ai
    - 未来也可在成功后把关键摘要写入 db9.ai
    """

    _state_repo = MemoryStateRepository()

    def __init__(self) -> None:
        self.provider = DeepSeekProvider()
        self.state_repo = self._state_repo

    def handle(self, request: InvokeRequest) -> InvokeResponseData:
        try:
            init_request = InitRequest.from_invoke(request)
            init_request = self._normalize_time(init_request)

            prompt = self._build_prompt(init_request)

            try:
                # raw_text = self.provider.complete_prompt(
                #     prompt,
                #     temperature=0,
                #     max_tokens=600,
                # )
                raw_text = self.provider.complete_prompt(
                    prompt,
                    temperature=0,
                    max_tokens=1200,
                )
                print("===== LLM RAW OUTPUT START =====")
                print(raw_text)
                print("===== LLM RAW OUTPUT END =====")
            except Exception as exc:
                raise LLMInvokeError(f"DeepSeek invoke failed: {exc}") from exc

            if not raw_text or not raw_text.strip():
                raise LLMEmptyResponseError("DeepSeek returned empty content")

            data = parse_json_object(raw_text)
            data = self._normalize_model_output(data)

            try:
                init_response = InitResponse.model_validate(data)
            except ValidationError as exc:
                raise LLMSchemaValidationError(f"InitResponse validation failed: {exc}") from exc

            response_payload = {
                "mainline": init_response.payload.mainline.model_dump(),
                "opening": init_response.payload.opening.model_dump(),
                "start_hint": init_response.payload.start_hint.model_dump(),
                "options": [item.model_dump() for item in init_response.payload.options],
            }

            self._save_state(init_request, init_response, response_payload)

            print(self.state_repo.get_snapshot(init_request.session.session_id)) # wait

            return InvokeResponseData(
                event=init_response.event,
                ai_state=init_response.ai_state.model_dump(),
                payload=response_payload,
                routing=init_response.routing.model_dump(),
                context=init_response.context.model_dump(),
                meta=init_response.meta.model_dump(),
            )   

        except (LLMEmptyResponseError, LLMJsonParseError, LLMSchemaValidationError, LLMInvokeError):
            raise
        except Exception as exc:
            raise RuntimeError(f"INIT handler failed: {exc}") from exc

    def _normalize_time(self, request: InitRequest) -> InitRequest:
        hard_limit_seconds = request.time.hard_limit_seconds
        elapsed_active_seconds = request.time.elapsed_active_seconds
        remaining_seconds = max(hard_limit_seconds - elapsed_active_seconds, 0)

        normalized_time = InitTime(
            hard_limit_seconds=hard_limit_seconds,
            elapsed_active_seconds=elapsed_active_seconds,
            remaining_seconds=remaining_seconds,
        )

        return request.model_copy(update={"time": normalized_time})

    def _build_prompt(self, request: InitRequest) -> str:
        prompt = render_init_prompt(request)

        augmented_context = self._build_augmented_context(request)
        if augmented_context:
            prompt = f"{prompt}\n\n【补充上下文】\n{augmented_context}"

        return prompt

    def _build_augmented_context(self, request: InitRequest) -> str:
        """
        db9.ai 预留入口：
        当前先只读取 request.context.memory_context。
        未来可在这里：
        1. 查询本地状态仓储
        2. 查询 db9.ai 召回结果
        3. 拼接增强上下文
        """
        parts: list[str] = []

        if request.context and request.context.memory_context:
            parts.append(str(request.context.memory_context))

        # 未来可在这里接 db9.ai / DuckDB / 其他增强信息
        return "\n".join(parts).strip()

    def _normalize_model_output(self, data: dict) -> dict:
        """
        只做轻量容错，不替模型补业务核心字段。
        允许修正：
        - event.type 大小写
        - routing.should_end 缺失时补默认 false
        """
        event = data.get("event")
        if isinstance(event, dict):
            event_type = event.get("type")
            if isinstance(event_type, str):
                event["type"] = event_type.lower()

        routing = data.get("routing")
        if isinstance(routing, dict) and "should_end" not in routing:
            routing["should_end"] = False

        return data

    def _save_state(
        self,
        request: InitRequest,
        response: InitResponse,
        response_payload: dict,
    ) -> None:
        """
        保存最小会话快照，供后续 LOOP 阶段使用。
        """
        session_id = request.session.session_id
        event_type = response.event.type.value
        ai_state = response.ai_state.model_dump()

        last_output = {
            "event": response.event.model_dump(),
            "payload": response_payload,
            "context": response.context.model_dump(),
        }

        self.state_repo.save_snapshot(
            session_id=session_id,
            event_type=event_type,
            ai_state=ai_state,
            last_output=last_output,
        )