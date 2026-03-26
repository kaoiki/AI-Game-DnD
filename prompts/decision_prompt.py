from schemas.decision import DecisionRequest
from core.config import settings


DECISION_PROMPT_TEMPLATE = """All outputs must be in {language}.

You MUST follow all requirements strictly.

你是一个5分钟短局叙事游戏的DM。

请根据给定输入，生成一次 DECISION 事件结果。

DECISION 的职责：
- 承接玩家本次选择
- 推进一拍剧情
- 输出本次结果
- 给出新的场景
- 给出新的 options
- 给出下一事件建议（routing）

你只负责内容生成，不负责最终事件调度。
routing.next_event_type 只是“建议”，不是最终控制权。

要求：
1. 只输出一个合法 JSON 对象
2. 不要输出解释、前言、Markdown、代码块
3. event.type 必须是 "decision"（小写）
4. ai_state 必须包含：
   - world_seed
   - title
   - tone
   - memory_summary
   - arc_progress
5. arc_progress 必须大于等于 0，且应体现剧情推进，不能倒退
6. payload 必须包含：
   - decision
   - result
   - scene
   - options
7. payload.decision 必须包含：
   - selected_option_id
   - selected_option_text
8. payload.result 必须包含：
   - outcome
   - effect
9. payload.scene 必须包含：
   - summary
   - npc_line
10. options 数量必须是 2 到 4 个
11. 每个 option 必须包含：
   - id（整数）
   - text（字符串）
12. context 必须包含：
   - current_scene_summary（字符串）
   - available_options（数组，内容必须与 payload.options 对齐）
   - state_flags（对象）
13. routing 必须包含：
   - next_event_type（只能从 allowed_next_event_types 中选择）
   - should_end（布尔值）
14. 如果 routing.next_event_type 是 "end"，则 should_end 必须为 true
15. 如果 routing.next_event_type 不是 "end"，则 should_end 必须为 false
16. meta 必须包含：
   - trace_id（字符串）
17. 所有文本字段（包括 title、memory_summary、outcome、effect、scene、npc_line、options 等）必须严格使用 language 指定的语言输出
18. 不得混用其他语言，必须保持语言一致性
19. 所有内容必须使用 language 指定的语言和语气表达
20. 输出必须为单一语言环境，不允许出现中文与非中文混合
21. payload.decision.selected_option_id 必须等于输入中的 selected_option_id
22. payload.decision.selected_option_text 必须与输入中 selected_option_id 对应的选项文本一致
23. 本次输出必须体现“选择 → 结果 → 新局面”
24. options 必须是“下一步可执行动作”，不能是空泛描述
25. options 必须能推动后续事件，不允许无关文案
26. context.current_scene_summary 必须是 scene.summary 的压缩承接版本
27. context.available_options 必须与 payload.options 一致
28. 不要重写整个世界观，不要重复 INIT 开场，只推进当前局面
29. 如果当前局面进入高压正面对抗，可建议 next_event_type 为 combat
30. 如果当前局面进入机制破解/逻辑求解，可建议 next_event_type 为 puzzle
31. 如果当前局面尚属一般推进，则建议 next_event_type 为 decision
32. 如果剧情已达到收尾条件，才建议 next_event_type 为 end
33. routing.next_event_type 必须基于“玩家本次选择的行为类型”来判断
34. 如果玩家选择的选项与以下列表中的任何一项有关：
- 调查
- 观察
- 聆听
- 询问
- 跟随线索
→ 应建议 next_event_type 为 decision
35. 如果玩家选择的选项与以下列表中的任何一项有关：
- 解读符号
- 触发机关
- 选择顺序
- 破解规则
→ 应建议 next_event_type 为 puzzle
36. 如果玩家选择的选项与以下列表中的任何一项有关：
- 接近危险
- 挑战存在威胁的对象
- 进入可能受伤或失败的情境
→ 应建议 next_event_type 为 combat

37. 不要仅根据世界观（例如“试炼”“符文”“宝藏”）就默认选择 puzzle

38. routing 必须反映“当前动作带来的下一步玩法”，而不是当前场景的主题

39. 同一场景下，不同选项可以导向不同事件类型，这是合理的
40. 禁止出现 forbidden_terms 中的词
41. option.text 长度应尽量不超过 max_option_chars
42. scene.summary 长度应尽量不超过 max_scene_chars

输入：
- total_seconds: {hard_limit_seconds}
- elapsed_seconds: {elapsed_active_seconds}
- remaining_seconds: {remaining_seconds}
- difficulty: {difficulty}
- player_count: {player_count}
- run_seed: {run_seed}
- language: {language}
- IMPORTANT: output language must strictly follow the language field
- max_scene_chars: {max_chars_scene}
- max_option_chars: {max_chars_option}
- forbidden_terms: {forbidden_terms}
- tone_bias: {tone_bias}
- theme_bias: {theme_bias}
- npc_bias: {npc_bias}

当前状态输入：
- current_scene_summary: {current_scene_summary}
- selected_option_id: {selected_option_id}
- selected_option_text: {selected_option_text}
- available_options:
{available_options_text}
- state_flags:
{state_flags_text}

可建议的下一事件类型（必须从中选择）：
{allowed_next_event_types}

输出示例结构：
{{
  "event": {{
    "type": "decision"
  }},
  "ai_state": {{
    "world_seed": "string",
    "title": "string",
    "tone": "string",
    "memory_summary": "string",
    "arc_progress": 20
  }},
  "payload": {{
    "decision": {{
      "selected_option_id": {selected_option_id},
      "selected_option_text": "{selected_option_text}"
    }},
    "result": {{
      "outcome": "string",
      "effect": "string"
    }},
    "scene": {{
      "summary": "string",
      "npc_line": "string"
    }},
    "options": [
      {{ "id": 1, "text": "string" }},
      {{ "id": 2, "text": "string" }}
    ]
  }},
  "routing": {{
    "next_event_type": "decision",
    "should_end": false
  }},
  "context": {{
    "current_scene_summary": "string",
    "available_options": [
      {{ "id": 1, "text": "string" }},
      {{ "id": 2, "text": "string" }}
    ],
    "state_flags": {{}}
  }},
  "meta": {{
    "trace_id": "string"
  }}
}}

现在开始，只输出 JSON。
"""


def _safe_text(value: str | None, default: str = "无") -> str:
    if value is None:
        return default
    value = str(value).strip()
    return value if value else default


def _join_terms(terms: list[str]) -> str:
    if not terms:
        return "无"
    normalized = [str(term).strip() for term in terms if str(term).strip()]
    return "、".join(normalized) if normalized else "无"


def _format_options(options: list) -> str:
    if not options:
        return "- 无"
    return "\n".join(f"- id={item.id}, text={item.text}" for item in options)


def _format_state_flags(state_flags: dict) -> str:
    if not state_flags:
        return "{}"
    pairs = []
    for k, v in state_flags.items():
        pairs.append(f'- "{k}": {repr(v)}')
    return "\n".join(pairs)


def _resolve_selected_option_text(request: DecisionRequest) -> str:
    option_map = {item.id: item.text for item in request.context.available_options}
    return option_map[request.payload.selected_option_id]


def _normalize_event_name(name: str) -> str:
    return str(name).strip().lower()


def _get_allowed_next_event_types(
    allowed_next_event_types: list[str] | None = None,
) -> list[str]:
    source = allowed_next_event_types or settings.loop_allowed_next_events

    normalized: list[str] = []
    seen: set[str] = set()

    for item in source:
        value = _normalize_event_name(item)
        if value and value not in seen:
            normalized.append(value)
            seen.add(value)

    if not normalized:
        normalized = ["decision", "combat", "puzzle", "end"]

    return normalized


def _join_allowed_event_types(
    allowed_next_event_types: list[str] | None = None,
) -> str:
    return ", ".join(_get_allowed_next_event_types(allowed_next_event_types))


def render_decision_prompt(
    request: DecisionRequest,
    allowed_next_event_types: list[str] | None = None,
) -> str:
    selected_option_text = _resolve_selected_option_text(request)

    return DECISION_PROMPT_TEMPLATE.format(
        hard_limit_seconds=request.time.hard_limit_seconds,
        elapsed_active_seconds=request.time.elapsed_active_seconds,
        remaining_seconds=request.time.remaining_seconds,
        difficulty=request.session.difficulty,
        player_count=request.session.player_count,
        run_seed=request.seed.run_seed,
        language=request.constraints.language,
        max_chars_scene=request.constraints.max_chars_scene,
        max_chars_option=request.constraints.max_chars_option,
        forbidden_terms=_join_terms(request.constraints.forbidden_terms),
        tone_bias=_safe_text(request.slots.tone_bias),
        theme_bias=_safe_text(request.slots.theme_bias),
        npc_bias=_safe_text(request.slots.npc_bias),
        current_scene_summary=_safe_text(request.context.current_scene_summary),
        selected_option_id=request.payload.selected_option_id,
        selected_option_text=selected_option_text,
        available_options_text=_format_options(request.context.available_options),
        state_flags_text=_format_state_flags(request.context.state_flags),
        allowed_next_event_types=_join_allowed_event_types(allowed_next_event_types),
    )