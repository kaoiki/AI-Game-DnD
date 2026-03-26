import uuid

from pydantic import ValidationError

from core.config import settings
from core.llm_exceptions import (
    LLMEmptyResponseError,
    LLMInvokeError,
    LLMJsonParseError,
    LLMSchemaValidationError,
)
from events.base import BaseEventHandler
from prompts.puzzle_prompt import render_puzzle_prompt
from repositories.memory_state_repository import MemoryStateRepository
from schemas.init import InitTime
from schemas.invoke import InvokeRequest, InvokeResponseData
from schemas.puzzle import PuzzleRequest, PuzzleResponse
from services.ai.deepseek_client import DeepSeekProvider
from utils.json_parser import parse_json_object


class PuzzleEventHandler(BaseEventHandler):
    """
    PUZZLE 事件处理器。

    职责：
    1. InvokeRequest -> PuzzleRequest
    2. 归一化 time
    3. 构建 prompt
    4. 调用 DeepSeek
    5. JSON parse
    6. 输出轻量归一化
    7. routing 校验
    8. schema 校验
    9. 返回统一 InvokeResponseData
    10. 保存最小状态快照
    """

    _state_repo = MemoryStateRepository()

    def __init__(self) -> None:
        self.provider = DeepSeekProvider()
        self.state_repo = self._state_repo

    def handle(self, request: InvokeRequest) -> InvokeResponseData:
        try:
            puzzle_request = PuzzleRequest.from_invoke(request)
            puzzle_request = self._normalize_time(puzzle_request)

            prompt = self._build_prompt(puzzle_request)

            try:
                raw_text = self.provider.complete_prompt(
                    prompt,
                    temperature=0,
                    max_tokens=1200,
                )
                print("===== PUZZLE LLM RAW OUTPUT START =====")
                print(raw_text)
                print("===== PUZZLE LLM RAW OUTPUT END =====")
            except Exception as exc:
                raise LLMInvokeError(f"DeepSeek invoke failed: {exc}") from exc

            if not raw_text or not raw_text.strip():
                raise LLMEmptyResponseError("DeepSeek returned empty content")

            data = parse_json_object(raw_text)
            data = self._normalize_model_output(puzzle_request, data)

            try:
                puzzle_response = PuzzleResponse.model_validate(data)
            except ValidationError as exc:
                raise LLMSchemaValidationError(
                    f"PuzzleResponse validation failed: {exc}"
                ) from exc

            response_payload = {
                "puzzle": puzzle_response.payload.puzzle.model_dump(),
                "attempt": puzzle_response.payload.attempt.model_dump(),
                "result": puzzle_response.payload.result.model_dump(),
                "scene": puzzle_response.payload.scene.model_dump(),
                "options": [
                    item.model_dump() for item in puzzle_response.payload.options
                ],
            }

            self._save_state(puzzle_request, puzzle_response, response_payload)

            print(self.state_repo.get_snapshot(puzzle_request.session.session_id))

            return InvokeResponseData(
                event=puzzle_response.event,
                ai_state=puzzle_response.ai_state.model_dump(),
                payload=response_payload,
                routing=puzzle_response.routing.model_dump(),
                context=puzzle_response.context.model_dump(),
                meta=puzzle_response.meta.model_dump(),
            )

        except (
            LLMEmptyResponseError,
            LLMJsonParseError,
            LLMSchemaValidationError,
            LLMInvokeError,
        ):
            raise
        except Exception as exc:
            raise RuntimeError(f"PUZZLE handler failed: {exc}") from exc

    def _normalize_time(self, request: PuzzleRequest) -> PuzzleRequest:
        hard_limit_seconds = request.time.hard_limit_seconds
        elapsed_active_seconds = request.time.elapsed_active_seconds
        remaining_seconds = max(hard_limit_seconds - elapsed_active_seconds, 0)

        normalized_time = InitTime(
            hard_limit_seconds=hard_limit_seconds,
            elapsed_active_seconds=elapsed_active_seconds,
            remaining_seconds=remaining_seconds,
        )

        return request.model_copy(update={"time": normalized_time})

    def _build_prompt(self, request: PuzzleRequest) -> str:
        prompt = render_puzzle_prompt(
            request,
            allowed_next_event_types=settings.loop_allowed_next_events,
        )

        augmented_context = self._build_augmented_context(request)
        if augmented_context:
            prompt = f"{prompt}\n\n【补充上下文】\n{augmented_context}"

        return prompt

    def _build_augmented_context(self, request: PuzzleRequest) -> str:
        """
        增强上下文预留入口。

        当前策略：
        - 优先读取状态仓储中的上一次快照
        - 拼接最小必要历史信息，帮助模型保持连续性
        - 不改动主协议，只作为 prompt 补充文本
        """
        parts: list[str] = []

        snapshot = self.state_repo.get_snapshot(request.session.session_id)
        if snapshot:
            prev_event_type = snapshot.get("event_type")
            ai_state = snapshot.get("ai_state") or {}
            last_output = snapshot.get("last_output") or {}
            prev_context = last_output.get("context") or {}

            if prev_event_type:
                parts.append(f"上一事件类型：{prev_event_type}")
            if ai_state.get("memory_summary"):
                parts.append(f"上一阶段剧情摘要：{ai_state['memory_summary']}")
            if prev_context.get("current_scene_summary"):
                parts.append(
                    f"上一阶段场景摘要：{prev_context['current_scene_summary']}"
                )

        return "\n".join(parts).strip()

    def _normalize_model_output(
        self,
        request: PuzzleRequest,
        data: dict,
    ) -> dict:
        """
        轻量归一化策略：
        - event.type 强制为 puzzle
        - payload.attempt 强制对齐输入 selected_option_id / text
        - routing.next_event_type 按配置兜底
        - should_end 与 next_event_type 保持一致
        - deadly -> 强制 end
        - enemy_triggered -> 强制 combat
        - payload.options 与 context.available_options 对齐
        - meta.trace_id 缺失时自动补
        """
        event = data.get("event")
        if not isinstance(event, dict):
            event = {}
            data["event"] = event
        event["type"] = "puzzle"

        selected_option_text = self._resolve_selected_option_text(request)

        payload = data.get("payload")
        if not isinstance(payload, dict):
            payload = {}
            data["payload"] = payload

        attempt = payload.get("attempt")
        if not isinstance(attempt, dict):
            attempt = {}
            payload["attempt"] = attempt

        attempt["selected_option_id"] = request.payload.selected_option_id
        attempt["selected_option_text"] = selected_option_text

        result = payload.get("result")
        if not isinstance(result, dict):
            result = {}
            payload["result"] = result

        failure_level = result.get("failure_level")
        if isinstance(failure_level, str):
            failure_level = failure_level.strip().lower()
        else:
            failure_level = "none"

        if failure_level not in {"none", "minor", "major", "deadly"}:
            failure_level = "none"
        result["failure_level"] = failure_level

        enemy_triggered = result.get("enemy_triggered")
        if not isinstance(enemy_triggered, bool):
            enemy_triggered = False
        result["enemy_triggered"] = enemy_triggered

        scene = payload.get("scene")
        if not isinstance(scene, dict):
            scene = {}
            payload["scene"] = scene

        if not scene.get("summary"):
            scene["summary"] = request.context.current_scene_summary

        options = payload.get("options")
        if not isinstance(options, list) or not options:
            options = [
                {"id": item.id, "text": item.text}
                for item in request.context.available_options
            ]
            payload["options"] = options

        context = data.get("context")
        if not isinstance(context, dict):
            context = {}
            data["context"] = context

        if not context.get("current_scene_summary"):
            context["current_scene_summary"] = scene["summary"]

        context["available_options"] = payload["options"]

        state_flags = context.get("state_flags")
        if not isinstance(state_flags, dict):
            context["state_flags"] = request.context.state_flags or {}

        routing = data.get("routing")
        if not isinstance(routing, dict):
            routing = {}
            data["routing"] = routing

        next_event_type = routing.get("next_event_type")
        if isinstance(next_event_type, str):
            next_event_type = next_event_type.strip().lower()
        else:
            next_event_type = None

        allowed = [
            str(item).strip().lower()
            for item in settings.loop_allowed_next_events
            if str(item).strip()
        ]
        fallback_non_end = "decision" if "decision" in allowed else (
            allowed[0] if allowed else "decision"
        )

        # 强语义规则优先级最高：
        # 1. deadly -> end
        # 2. enemy_triggered -> combat
        if failure_level == "deadly":
            next_event_type = "end" if "end" in allowed else fallback_non_end
        elif enemy_triggered:
            next_event_type = "combat" if "combat" in allowed else fallback_non_end
        else:
            if not next_event_type:
                next_event_type = fallback_non_end

            if next_event_type not in allowed:
                if routing.get("should_end") is True and "end" in allowed:
                    next_event_type = "end"
                else:
                    next_event_type = fallback_non_end

        routing["next_event_type"] = next_event_type
        routing["should_end"] = next_event_type == "end"

        meta = data.get("meta")
        if not isinstance(meta, dict):
            meta = {}
            data["meta"] = meta

        if not meta.get("trace_id"):
            meta["trace_id"] = f"puzzle_{request.seed.run_seed}_{uuid.uuid4().hex[:8]}"

        return data

    def _resolve_selected_option_text(self, request: PuzzleRequest) -> str:
        option_map = {item.id: item.text for item in request.context.available_options}
        return option_map[request.payload.selected_option_id]

    def _save_state(
        self,
        request: PuzzleRequest,
        response: PuzzleResponse,
        response_payload: dict,
    ) -> None:
        """
        保存最小会话快照，供后续 LOOP 阶段继续使用。
        """
        session_id = request.session.session_id
        event_type = response.event.type.value
        ai_state = response.ai_state.model_dump()

        last_output = {
            "event": response.event.model_dump(),
            "payload": response_payload,
            "context": response.context.model_dump(),
            "routing": response.routing.model_dump(),
            "meta": response.meta.model_dump(),
        }

        self.state_repo.save_snapshot(
            session_id=session_id,
            event_type=event_type,
            ai_state=ai_state,
            last_output=last_output,
        )