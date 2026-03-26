import random

from schemas.init import InitRequest
from core.config import settings


INIT_PROMPT_TEMPLATE = """All outputs must be in {language}.

You MUST follow all requirements strictly.

你是一个5分钟短局叙事游戏的DM。

请根据给定输入，生成一次 INIT 事件结果。

要求：
1. 只输出一个合法 JSON 对象
2. 不要输出解释、前言、Markdown、代码块
3. event.type 必须是 "init"（小写）
4. ai_state 必须包含：
   - world_seed
   - title
   - tone
   - memory_summary
   - arc_progress
5. arc_progress 必须是 0
6. payload 必须包含：
   - mainline
   - opening
   - start_hint
   - options
7. payload.mainline 必须包含：
   - premise
   - player_role
   - primary_goal
   - stakes
8. payload.opening 必须包含：
   - scene
   - npc_line
9. payload.start_hint 必须包含：
   - how_to_play_next
10. options 数量必须是 2 到 4 个
11. 每个 option 必须包含：
   - id（整数）
   - text（字符串）
12. context 必须包含：
   - current_scene_summary（字符串）
   - available_options（数组，内容应与 payload.options 对齐）
   - state_flags（对象）
13. routing 必须包含：
   - next_event_type（只能从 allowed_next_event_types 中选择）
   - should_end（布尔值，INIT 默认 false）
14. meta 必须包含：
   - trace_id（字符串）
15. 所有文本字段（包括 title、scene、npc_line、options 等）必须严格使用 language 指定的语言输出
16. 不得混用其他语言，必须保持语言一致性
17. 所有内容必须使用 language 指定的语言和语气表达
18. ai_state、payload 内所有字符串字段必须统一使用 language 指定的语言输出，不允许部分字段使用其他语言
19. 输出必须为单一语言环境，不允许出现中文与非中文混合
20. routing.next_event_type 必须从 allowed_next_event_types 中选择
21. INIT 不应直接结束，should_end 必须为 false

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

可建议的下一事件类型（必须从中选择）：
{allowed_next_event_types}

输出示例中的 next_event_type 样例值（仅示例，不代表固定写死）：
{sample_next_event_type}

输出示例结构：
{{
  "event": {{
    "type": "init"
  }},
  "ai_state": {{
    "world_seed": "string",
    "title": "string",
    "tone": "string",
    "memory_summary": "string",
    "arc_progress": 0
  }},
  "payload": {{
    "mainline": {{
      "premise": "string",
      "player_role": "string",
      "primary_goal": "string",
      "stakes": "string"
    }},
    "opening": {{
      "scene": "string",
      "npc_line": "string"
    }},
    "start_hint": {{
      "how_to_play_next": "string"
    }},
    "options": [
      {{ "id": 1, "text": "string" }},
      {{ "id": 2, "text": "string" }}
    ]
  }},
  "routing": {{
    "next_event_type": "{sample_next_event_type}",
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


def _normalize_event_name(name: str) -> str:
    return str(name).strip().lower()


def _get_allowed_next_event_types(
    allowed_next_event_types: list[str] | None = None,
) -> list[str]:
    source = allowed_next_event_types or settings.init_allowed_next_events

    normalized: list[str] = []
    seen: set[str] = set()

    for item in source:
        value = _normalize_event_name(item)
        if value and value not in seen:
            normalized.append(value)
            seen.add(value)

    if not normalized:
        normalized = ["decision", "combat", "puzzle"]

    return normalized


def _join_allowed_event_types(
    allowed_next_event_types: list[str] | None = None,
) -> str:
    return ", ".join(_get_allowed_next_event_types(allowed_next_event_types))


def _sample_next_event_type(
    allowed_next_event_types: list[str] | None = None,
) -> str:
    candidates = _get_allowed_next_event_types(allowed_next_event_types)
    return random.choice(candidates)


def render_init_prompt(
    request: InitRequest,
    allowed_next_event_types: list[str] | None = None,
) -> str:
    sample_next_event_type = _sample_next_event_type(allowed_next_event_types)

    return INIT_PROMPT_TEMPLATE.format(
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
        allowed_next_event_types=_join_allowed_event_types(allowed_next_event_types),
        sample_next_event_type=sample_next_event_type,
    )