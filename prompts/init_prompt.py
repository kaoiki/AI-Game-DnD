from schemas.init import InitRequest

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
12. routing 必须包含：
   - next_event_type（只能是 DECISION、COMBAT、PUZZLE、END）
   - should_end（布尔值，INIT 默认 false）
13. meta 必须包含：
   - trace_id（字符串）
14. 所有文本字段（包括 title、scene、npc_line、options 等）必须严格使用 language 指定的语言输出
15. 不得混用其他语言，必须保持语言一致性
16. 所有内容必须使用 language 指定的语言和语气表达
18. ai_state、payload 内所有字符串字段必须统一使用 language 指定的语言输出，不允许部分字段使用其他语言
19. 输出必须为单一语言环境，不允许出现中英文混合

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
    "next_event_type": "DECISION",
    "should_end": false
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
    return "、".join(terms)


def render_init_prompt(request: InitRequest) -> str:
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
    )