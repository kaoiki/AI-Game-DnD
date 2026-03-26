import uuid
from typing import Any

from pydantic import ValidationError

from core.llm_exceptions import (
    LLMEmptyResponseError,
    LLMInvokeError,
    LLMJsonParseError,
    LLMSchemaValidationError,
)
from events.base import BaseEventHandler
from prompts.end_prompt import render_end_prompt
from repositories.memory_state_repository import MemoryStateRepository
from schemas.end import EndRequest, EndResponse
from schemas.init import InitTime
from schemas.invoke import InvokeRequest, InvokeResponseData
from services.ai.deepseek_client import DeepSeekProvider
from utils.json_parser import parse_json_object


class EndEventHandler(BaseEventHandler):
    """
    END 事件处理器。

    职责：
    1. InvokeRequest -> EndRequest
    2. 归一化 time
    3. 构建 prompt（注入整局历史摘要）
    4. 调用 DeepSeek
    5. JSON parse
    6. 输出轻量归一化
    7. schema 校验
    8. 返回统一 InvokeResponseData
    9. 保存最终状态快照
    """

    _state_repo = MemoryStateRepository()

    def __init__(self) -> None:
        self.provider = DeepSeekProvider()
        self.state_repo = self._state_repo

    def handle(self, request: InvokeRequest) -> InvokeResponseData:
        try:
            end_request = EndRequest.from_invoke(request)
            end_request = self._normalize_time(end_request)

            history_events = self._collect_history_events(end_request)
            prompt = self._build_prompt(end_request, history_events)

            try:
                raw_text = self.provider.complete_prompt(
                    prompt,
                    temperature=0,
                    max_tokens=1400,
                )
                print("===== END LLM RAW OUTPUT START =====")
                print(raw_text)
                print("===== END LLM RAW OUTPUT END =====")
            except Exception as exc:
                raise LLMInvokeError(f"DeepSeek invoke failed: {exc}") from exc

            if not raw_text or not raw_text.strip():
                raise LLMEmptyResponseError("DeepSeek returned empty content")

            data = parse_json_object(raw_text)
            data = self._normalize_model_output(end_request, data, history_events)

            try:
                end_response = EndResponse.model_validate(data)
            except ValidationError as exc:
                raise LLMSchemaValidationError(
                    f"EndResponse validation failed: {exc}"
                ) from exc

            response_payload = {
                "ending": end_response.payload.ending.model_dump(),
                "epilogue": end_response.payload.epilogue.model_dump(),
                "key_choices": [
                    item.model_dump() for item in end_response.payload.key_choices
                ],
                "novel_summary": end_response.payload.novel_summary.model_dump(),
            }

            self._save_state(end_request, end_response, response_payload)

            print(self.state_repo.get_snapshot(end_request.session.session_id))

            return InvokeResponseData(
                event=end_response.event,
                ai_state=end_response.ai_state.model_dump(),
                payload=response_payload,
                routing=end_response.routing.model_dump(),
                context=end_response.context.model_dump(),
                meta=end_response.meta.model_dump(),
            )

        except (
            LLMEmptyResponseError,
            LLMJsonParseError,
            LLMSchemaValidationError,
            LLMInvokeError,
        ):
            raise
        except Exception as exc:
            raise RuntimeError(f"END handler failed: {exc}") from exc

    def _normalize_time(self, request: EndRequest) -> EndRequest:
        hard_limit_seconds = request.time.hard_limit_seconds
        elapsed_active_seconds = request.time.elapsed_active_seconds
        remaining_seconds = max(hard_limit_seconds - elapsed_active_seconds, 0)

        normalized_time = InitTime(
            hard_limit_seconds=hard_limit_seconds,
            elapsed_active_seconds=elapsed_active_seconds,
            remaining_seconds=remaining_seconds,
        )

        return request.model_copy(update={"time": normalized_time})

    def _build_prompt(
        self,
        request: EndRequest,
        history_events: list[dict[str, Any]],
    ) -> str:
        prompt = render_end_prompt(
            request,
            history_events=history_events,
        )

        augmented_context = self._build_augmented_context(request)
        if augmented_context:
            prompt = f"{prompt}\n\n【补充上下文】\n{augmented_context}"

        return prompt

    def _build_augmented_context(self, request: EndRequest) -> str:
        """
        END 的补充上下文入口。

        当前策略：
        - 读取最近一次快照，补充上一阶段摘要
        - 不改主协议，只作为 prompt 补充文本
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

    def _collect_history_events(self, request: EndRequest) -> list[dict[str, Any]]:
        """
        收集 END 用于总结整局的最小历史链。

        当前仓储只有“最近一次快照”，所以这里采用保底策略：
        1. 优先从 request.context.history_events 读取（如果你在 end schema 里预留了该字段）
        2. 否则回退到 state_repo 中最后一次快照
        3. 再不行就只用当前 context 生成最小历史

        这样可以先让 END 跑通，后续你若把完整事件链写入仓储，这里再升级即可。
        """
        history_events = getattr(request.context, "history_events", None)
        if isinstance(history_events, list) and history_events:
            normalized: list[dict[str, Any]] = []
            for item in history_events:
                if hasattr(item, "model_dump"):
                    normalized.append(item.model_dump())
                elif isinstance(item, dict):
                    normalized.append(item)
            if normalized:
                return normalized

        snapshot = self.state_repo.get_snapshot(request.session.session_id)
        if snapshot:
            last_output = snapshot.get("last_output") or {}
            payload = last_output.get("payload") or {}
            context = last_output.get("context") or {}
            event = last_output.get("event") or {}

            selected_option_text = self._extract_selected_option_text(payload)

            return [
                {
                    "event_type": event.get("type", snapshot.get("event_type", "unknown")),
                    "scene_summary": context.get(
                        "current_scene_summary",
                        request.context.current_scene_summary,
                    ),
                    "selected_option_text": selected_option_text,
                    "result_summary": self._extract_result_summary(payload),
                }
            ]

        return [
            {
                "event_type": "unknown",
                "scene_summary": request.context.current_scene_summary,
                "selected_option_text": "",
                "result_summary": "",
            }
        ]

    def _extract_selected_option_text(self, payload: dict[str, Any]) -> str:
        if not isinstance(payload, dict):
            return ""

        decision = payload.get("decision")
        if isinstance(decision, dict) and decision.get("selected_option_text"):
            return str(decision["selected_option_text"]).strip()

        attempt = payload.get("attempt")
        if isinstance(attempt, dict) and attempt.get("selected_option_text"):
            return str(attempt["selected_option_text"]).strip()

        combat = payload.get("combat")
        if isinstance(combat, dict) and combat.get("selected_option_text"):
            return str(combat["selected_option_text"]).strip()

        result = payload.get("result")
        if isinstance(result, dict) and result.get("player_action"):
            return str(result["player_action"]).strip()

        return ""

    def _extract_result_summary(self, payload: dict[str, Any]) -> str:
        if not isinstance(payload, dict):
            return ""

        result = payload.get("result")
        if isinstance(result, dict):
            for key in ("summary", "outcome", "resolution"):
                value = result.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

        scene = payload.get("scene")
        if isinstance(scene, dict):
            summary = scene.get("summary")
            if isinstance(summary, str) and summary.strip():
                return summary.strip()

        epilogue = payload.get("epilogue")
        if isinstance(epilogue, dict):
            scene_text = epilogue.get("scene")
            if isinstance(scene_text, str) and scene_text.strip():
                return scene_text.strip()

        return ""

    def _has_real_history_choice(self, history_events: list[dict[str, Any]]) -> bool:
            for item in history_events:
                choice_text = str(item.get("selected_option_text", "")).strip()
                if choice_text:
                    return True
            return False

    def _sanitize_choices_when_history_missing(
        self,
        normalized_choices: list[dict[str, Any]],
        has_real_choice: bool,
    ) -> list[dict[str, Any]]:
        """
        当历史里没有真实 choice 时，禁止保留 LLM 脑补出来的具体动作。
        """
        if has_real_choice:
            return normalized_choices

        if not normalized_choices:
            return [
                {
                    "event_type": "decision",
                    "choice_text": "未记录具体动作的关键抉择",
                    "impact": "虽然历史中没有保留明确选项文本，但这一步推进促成了故事的最终收束。",
                }
            ]

        sanitized: list[dict[str, Any]] = []
        for item in normalized_choices[:5]:
            event_type = str(item.get("event_type", "decision")).strip().lower() or "decision"
            impact = str(item.get("impact", "")).strip()
            if not impact:
                impact = "虽然历史中没有保留明确选项文本，但这一步推进促成了故事的最终收束。"

            sanitized.append(
                {
                    "event_type": event_type,
                    "choice_text": "未记录具体动作的关键抉择",
                    "impact": impact,
                }
            )

        return sanitized

    def _build_abstract_player_journey(self, fallback_scene: str) -> str:
        """
        当历史里没有真实 selected_option_text 时，
        强制使用抽象摘要，禁止保留 LLM 脑补出的具体动作或心理路径。
        """
        return (
            f"玩家在旅程末段持续推动局势发展，并最终抵达“{fallback_scene}”所指向的终局场景。"
        )

    def _normalize_model_output(
        self,
        request: EndRequest,
        data: dict,
        history_events: list[dict[str, Any]],
    ) -> dict:
        """
        END 专用轻量归一化策略：
        - event.type 强制为 end
        - routing 固定为终局态
        - context.available_options 强制为空数组
        - current_scene_summary 兜底为 epilogue.scene
        - key_choices 为空时，根据 history_events 做最小保底
        - meta.trace_id 缺失时自动补
        """
        event = data.get("event")
        if not isinstance(event, dict):
            event = {}
            data["event"] = event
        event["type"] = "end"

        payload = data.get("payload")
        if not isinstance(payload, dict):
            payload = {}
            data["payload"] = payload

        ending = payload.get("ending")
        if not isinstance(ending, dict):
            ending = {}
            payload["ending"] = ending

        if not ending.get("title"):
            ending["title"] = "终局"
        if not ending.get("outcome"):
            ending["outcome"] = "你的冒险在此刻落下帷幕。"

        epilogue = payload.get("epilogue")
        if not isinstance(epilogue, dict):
            epilogue = {}
            payload["epilogue"] = epilogue

        if not epilogue.get("scene"):
            epilogue["scene"] = request.context.current_scene_summary
        if not epilogue.get("closing_line"):
            epilogue["closing_line"] = "故事到这里，终于迎来了它的结尾。"

        key_choices = payload.get("key_choices")
        if not isinstance(key_choices, list):
            key_choices = []
            payload["key_choices"] = key_choices

        normalized_choices: list[dict[str, Any]] = []
        for item in key_choices:
            if not isinstance(item, dict):
                continue

            event_type = str(item.get("event_type", "decision")).strip().lower() or "decision"
            choice_text = str(item.get("choice_text", "")).strip()
            impact = str(item.get("impact", "")).strip()

            if not choice_text:
                continue
            if not impact:
                impact = "这一选择推动了故事走向最终结局。"

            normalized_choices.append(
                {
                    "event_type": event_type,
                    "choice_text": choice_text,
                    "impact": impact,
                }
            )

        has_real_choice = self._has_real_history_choice(history_events)

        if has_real_choice:
            if not normalized_choices:
                for item in history_events[:5]:
                    choice_text = str(item.get("selected_option_text", "")).strip()
                    if not choice_text:
                        continue
                    normalized_choices.append(
                        {
                            "event_type": str(item.get("event_type", "decision")).strip().lower() or "decision",
                            "choice_text": choice_text,
                            "impact": "这一选择影响了你最终抵达的结局。",
                        }
                    )
            payload["key_choices"] = normalized_choices[:5]
        else:
            payload["key_choices"] = self._sanitize_choices_when_history_missing(
                normalized_choices=normalized_choices,
                has_real_choice=False,
            )

        novel_summary = payload.get("novel_summary")
        if not isinstance(novel_summary, dict):
            novel_summary = {}
            payload["novel_summary"] = novel_summary

        if not novel_summary.get("story_overview"):
            novel_summary["story_overview"] = request.context.current_scene_summary

        has_real_choice = self._has_real_history_choice(history_events)
        if has_real_choice:
            if not novel_summary.get("player_journey"):
                novel_summary["player_journey"] = self._build_player_journey_text(
                    history_events=history_events,
                    fallback_scene=request.context.current_scene_summary,
                )
        else:
            novel_summary["player_journey"] = self._build_abstract_player_journey(
                fallback_scene=request.context.current_scene_summary,
            )

        if not novel_summary.get("final_outcome"):
            novel_summary["final_outcome"] = ending["outcome"]

        context = data.get("context")
        if not isinstance(context, dict):
            context = {}
            data["context"] = context

        if not context.get("current_scene_summary"):
            context["current_scene_summary"] = epilogue["scene"]

        context["available_options"] = []

        state_flags = context.get("state_flags")
        if not isinstance(state_flags, dict):
            context["state_flags"] = request.context.state_flags or {}

        request_history_events = getattr(request.context, "history_events", None)
        if request_history_events:
            context["history_events"] = [
                item.model_dump() if hasattr(item, "model_dump") else item
                for item in request_history_events
            ]
        else:
            context["history_events"] = history_events or None

        routing = data.get("routing")
        if not isinstance(routing, dict):
            routing = {}
            data["routing"] = routing

        routing["next_event_type"] = "end"
        routing["should_end"] = True

        meta = data.get("meta")
        if not isinstance(meta, dict):
            meta = {}
            data["meta"] = meta

        if not meta.get("trace_id"):
            meta["trace_id"] = f"end_{request.seed.run_seed}_{uuid.uuid4().hex[:8]}"

        return data

    def _build_player_journey_text(
        self,
        history_events: list[dict[str, Any]],
        fallback_scene: str,
    ) -> str:
        parts: list[str] = []

        for item in history_events:
            scene = str(item.get("scene_summary", "")).strip()
            choice = str(item.get("selected_option_text", "")).strip()
            result = str(item.get("result_summary", "")).strip()

            seg = []
            if scene:
                seg.append(scene)
            if choice:
                seg.append(f"你做出了“{choice}”这一选择")
            if result:
                seg.append(result)

            if seg:
                parts.append("，".join(seg))

        if not parts:
            return f"玩家在旅程末段持续推动局势前进，并最终抵达“{fallback_scene}”所指向的终局场景。"

        return "；".join(parts)

    def _save_state(
        self,
        request: EndRequest,
        response: EndResponse,
        response_payload: dict,
    ) -> None:
        """
        保存最终会话快照，供后续 NOVEL 接口复用。
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