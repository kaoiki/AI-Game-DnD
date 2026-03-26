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
from prompts.combat_prompt import render_combat_prompt
from repositories.memory_state_repository import MemoryStateRepository
from schemas.combat import CombatRequest, CombatResponse
from schemas.init import InitTime
from schemas.invoke import InvokeRequest, InvokeResponseData
from services.ai.deepseek_client import DeepSeekProvider
from utils.json_parser import parse_json_object


class CombatEventHandler(BaseEventHandler):
    """
    COMBAT 事件处理器。

    职责：
    1. InvokeRequest -> CombatRequest
    2. 归一化 time
    3. 构建 prompt
    4. 调用 DeepSeek
    5. JSON parse
    6. 输出轻量归一化
    7. schema 校验
    8. 返回统一 InvokeResponseData
    9. 保存最小状态快照
    """

    _state_repo = MemoryStateRepository()

    def __init__(self) -> None:
        self.provider = DeepSeekProvider()
        self.state_repo = self._state_repo

    def handle(self, request: InvokeRequest) -> InvokeResponseData:
        try:
            combat_request = CombatRequest.from_invoke(request)
            combat_request = self._normalize_time(combat_request)

            prompt = self._build_prompt(combat_request)

            try:
                raw_text = self.provider.complete_prompt(
                    prompt,
                    temperature=0,
                    max_tokens=1200,
                )
                print("===== COMBAT LLM RAW OUTPUT START =====")
                print(raw_text)
                print("===== COMBAT LLM RAW OUTPUT END =====")
            except Exception as exc:
                raise LLMInvokeError(f"DeepSeek invoke failed: {exc}") from exc

            if not raw_text or not raw_text.strip():
                raise LLMEmptyResponseError("DeepSeek returned empty content")

            data = parse_json_object(raw_text)
            data = self._normalize_model_output(combat_request, data)

            try:
                combat_response = CombatResponse.model_validate(data)
            except ValidationError as exc:
                raise LLMSchemaValidationError(
                    f"CombatResponse validation failed: {exc}"
                ) from exc

            response_payload = {
                "result": combat_response.payload.result.model_dump(),
                "scene": combat_response.payload.scene.model_dump(),
                "options": [
                    item.model_dump() for item in combat_response.payload.options
                ],
            }

            self._save_state(combat_request, combat_response, response_payload)

            print(self.state_repo.get_snapshot(combat_request.session.session_id))

            return InvokeResponseData(
                event=combat_response.event,
                ai_state=combat_response.ai_state.model_dump(),
                payload=response_payload,
                routing=combat_response.routing.model_dump(),
                context=combat_response.context.model_dump(),
                meta=combat_response.meta.model_dump(),
            )

        except (
            LLMEmptyResponseError,
            LLMJsonParseError,
            LLMSchemaValidationError,
            LLMInvokeError,
        ):
            raise
        except Exception as exc:
            raise RuntimeError(f"COMBAT handler failed: {exc}") from exc

    def _normalize_time(self, request: CombatRequest) -> CombatRequest:
        hard_limit_seconds = request.time.hard_limit_seconds
        elapsed_active_seconds = request.time.elapsed_active_seconds
        remaining_seconds = max(hard_limit_seconds - elapsed_active_seconds, 0)

        normalized_time = InitTime(
            hard_limit_seconds=hard_limit_seconds,
            elapsed_active_seconds=elapsed_active_seconds,
            remaining_seconds=remaining_seconds,
        )

        return request.model_copy(update={"time": normalized_time})

    def _build_prompt(self, request: CombatRequest) -> str:
        prompt = render_combat_prompt(
            request,
            allowed_next_event_types=settings.loop_allowed_next_events,
        )

        augmented_context = self._build_augmented_context(request)
        if augmented_context:
            prompt = f"{prompt}\n\n【补充上下文】\n{augmented_context}"

        return prompt

    def _build_augmented_context(self, request: CombatRequest) -> str:
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
        request: CombatRequest,
        data: dict,
    ) -> dict:
        event = data.get("event")
        if not isinstance(event, dict):
            event = {}
            data["event"] = event
        event["type"] = "combat"

        payload = data.get("payload")
        if not isinstance(payload, dict):
            payload = {}
            data["payload"] = payload

        result = payload.get("result")
        if not isinstance(result, dict):
            result = {}
            payload["result"] = result

        option_text_map = {
            item.id: item.text for item in request.context.available_options
        }

        if not result.get("player_action"):
            result["player_action"] = option_text_map.get(
                request.payload.selected_option_id,
                f"选择了选项 {request.payload.selected_option_id}",
            )

        if not result.get("enemy_action"):
            result["enemy_action"] = "眼前的威胁发起反击"

        if not result.get("outcome"):
            result["outcome"] = "你与眼前的威胁继续周旋，局势仍在变化。"

        damage_to_enemy = result.get("damage_to_enemy")
        if not isinstance(damage_to_enemy, int):
            result["damage_to_enemy"] = 0
        else:
            result["damage_to_enemy"] = max(damage_to_enemy, 0)

        damage_to_player = result.get("damage_to_player")
        if not isinstance(damage_to_player, int):
            result["damage_to_player"] = 0
        else:
            result["damage_to_player"] = max(damage_to_player, 0)

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

        should_end = routing.get("should_end")
        if not isinstance(should_end, bool):
            should_end = False

        allowed = settings.loop_allowed_next_events
        fallback_non_end = "decision" if "decision" in allowed else (
            allowed[0] if allowed else "decision"
        )

        # 兜底规则：
        # 1. LLM 判定 should_end=true，则强制 end
        # 2. LLM 判定 next_event_type=end，则强制 should_end=true
        # 3. 其余情况必须落在 allowed 范围内
        if should_end:
            next_event_type = "end" if "end" in allowed else fallback_non_end
            should_end = next_event_type == "end"
        else:
            if next_event_type == "end":
                should_end = True
            else:
                if not next_event_type or next_event_type not in allowed:
                    next_event_type = fallback_non_end
                should_end = False

        routing["next_event_type"] = next_event_type
        routing["should_end"] = should_end

        meta = data.get("meta")
        if not isinstance(meta, dict):
            meta = {}
            data["meta"] = meta

        if not meta.get("trace_id"):
            meta["trace_id"] = f"combat_{request.seed.run_seed}_{uuid.uuid4().hex[:8]}"

        return data

    def _save_state(
        self,
        request: CombatRequest,
        response: CombatResponse,
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