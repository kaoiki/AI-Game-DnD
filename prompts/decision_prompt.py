from schemas.decision import DecisionRequest
from core.config import settings


DECISION_PROMPT_TEMPLATE = DECISION_PROMPT_TEMPLATE = """All outputs must be in {language}.

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

要求：
1. 只输出 JSON
2. event.type 必须是 "decision"

（中间原结构全部保持）

30. 如果当前局面进入机制破解 → puzzle
31. 如果当前局面进入对抗 → combat

32. 【强规则：终局判定（最高优先级）】
如果满足以下任一情况，必须直接结束：
- 玩家已完成目标
- 已脱离主要威胁
- 出现出口 / 终点 / 最终场景
- arc_progress >= 80 且剧情明显收束

则必须：
- routing.next_event_type = "end"
- routing.should_end = true

33. 【禁止拖延 decision】
不能为了“还有选项”而继续 decision

34. 【终局优先级高于行为类型】
即使行为属于探索/观察，只要接近终局 → end

35. 仅在未达到终局时，才允许继续 decision
36. 【强规则：避免连续 decision（最高优先级之一）】
如果当前局面已经经历过 decision，且本次 options 明显指向：
- 行动尝试 / 风险行为 → 必须转为 combat
- 机制互动 / 解法尝试 → 必须转为 puzzle

❗禁止连续两轮以上 decision（除非明确为纯信息补充且无风险）

【强规则：行为驱动分流】
必须根据 options 的语义强制分流：
- 包含攻击、突进、强行突破、冒险行为 → combat
- 包含解谜、操作机关、逻辑判断、破解 → puzzle
- 仅当为低风险探索或信息收集 → 才允许 decision

【禁止伪 decision】
不允许生成“本质是行动但仍标记为 decision”的内容
例如：
- 已经发生冲突却仍然 decision ❌
- 已进入解谜却仍然 decision ❌

【终局信号识别（必须 end）】
如果 scene 或 result 已经出现以下语义：
- “出口出现 / 已可离开”
- “目标已达成 / 核心问题已解决”
- “威胁已消失 / 局势稳定”

则必须：
- routing.next_event_type = "end"
- routing.should_end = true

❗禁止在上述情况下继续 decision

【decision 使用边界】
decision 只能用于：
- 信息获取
- 轻度探索
- 非直接风险选择

一旦进入关键推进阶段，必须切换到 combat 或 puzzle 或 end
37. 【强规则：npc_line 不可为空】
payload.scene.npc_line 必须始终输出非空字符串，至少 1 个字符

如果当前场景没有明确 NPC：
- 可以使用环境低语
- 可以使用自言自语
- 可以使用远处回声
- 可以使用系统提示式短句

❗禁止输出空字符串
❗禁止省略 npc_line

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