from core.config import settings
from schemas.combat import CombatRequest


COMBAT_PROMPT_TEMPLATE = """All outputs must be in {language}.

You MUST follow all requirements strictly.

你是一个5分钟短局叙事游戏的DM。

请根据给定输入，生成一次 COMBAT 事件结果。

COMBAT 的职责：
- 承接玩家本次选择
- 只推进一个回合结果
- 输出本回合结果
- 给出新的场景
- 给出新的 options
- 给出下一事件建议（routing）

你只负责内容生成，不负责最终事件调度。
routing.next_event_type 只是“建议”，不是最终控制权。

要求：
1. 只输出一个合法 JSON 对象
2. 不要输出解释、前言、Markdown、代码块
3. event.type 必须是 "combat"（小写）
4. ai_state 必须包含：
   - world_seed
   - title
   - tone
   - memory_summary
   - arc_progress
5. arc_progress 必须大于等于 0，且应体现剧情推进，不能倒退
6. COMBAT 是单回合事件：一次输出只允许推进 1 个回合结果
7. payload 必须只包含：
   - result
   - scene
   - options
8. payload.result 必须包含：
   - player_action
   - enemy_action
   - outcome
   - damage_to_enemy
   - damage_to_player
9. payload.scene 必须包含：
   - summary
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
17. 所有文本字段必须严格使用 language 指定的语言输出
18. 不得混用其他语言，必须保持语言一致性
19. 输出必须为单一语言环境，不允许出现中文与非中文混合
20. 敌人名称不从输入中读取，你必须根据 current_scene_summary 自行生成一个合理且统一的敌人称呼，并体现在 enemy_action、outcome、scene.summary 中
21. 你必须判断本回合结果是“玩家死亡”还是“玩家仍然活着”
22. 如果玩家死亡，则 routing.next_event_type 必须建议为 "end"，且 should_end 必须为 true
23. 如果玩家仍然活着，则 routing.next_event_type 必须从 allowed_next_event_types 中合理选择，且 should_end 必须为 false
24. 你必须根据“本回合结算后下一步 options 的语义”决定 routing.next_event_type，而不是机械根据当前事件名选择
25. 如果下一步 options 仍主要是在处理当前威胁，例如继续攻击、防守、闪避、反击、周旋、牵制、寻找弱点后进行攻击、在交战中呼叫支援等，则 next_event_type 应为 "combat"
26. 只有当“破解机制”已经成为下一步的核心玩法时，next_event_type 才应为 "puzzle"
27. 如果下一步 options 已经转为普通推进、探索、搜索、包扎、观察四周、检查战利品等，则 next_event_type 应为 "decision"
28. 如果已经形成终局，则 next_event_type 必须建议为 "end"
29. 不要重写整个世界观，不要重复 INIT 开场，只推进当前局面
30. 本回合结果必须体现“玩家动作 → 敌方反应 → 回合结算”
31. options 必须是“下一步可执行动作”，不能是空泛描述
32. options 必须能推动后续事件，不允许无关文案
33. options 的语义必须与 routing.next_event_type 保持一致
34. context.current_scene_summary 必须是 scene.summary 的压缩承接版本
35. context.available_options 必须与 payload.options 一致
36. 禁止出现 forbidden_terms 中的词
37. option.text 长度应尽量不超过 max_option_chars
38. scene.summary 长度应尽量不超过 max_scene_chars

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
- available_options:
{available_options_text}
- state_flags:
{state_flags_text}

可建议的下一事件类型（必须从中选择）：
{allowed_next_event_types}

输出示例结构：
{{
  "event": {{
    "type": "combat"
  }},
  "ai_state": {{
    "world_seed": "string",
    "title": "string",
    "tone": "string",
    "memory_summary": "string",
    "arc_progress": 20
  }},
  "payload": {{
    "result": {{
      "player_action": "string",
      "enemy_action": "string",
      "outcome": "string",
      "damage_to_enemy": 2,
      "damage_to_player": 1
    }},
    "scene": {{
      "summary": "string"
    }},
    "options": [
      {{ "id": 1, "text": "string" }},
      {{ "id": 2, "text": "string" }}
    ]
  }},
  "routing": {{
    "next_event_type": "combat",
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


def render_combat_prompt(
    request: CombatRequest,
    allowed_next_event_types: list[str] | None = None,
) -> str:
    return COMBAT_PROMPT_TEMPLATE.format(
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
        available_options_text=_format_options(request.context.available_options),
        state_flags_text=_format_state_flags(request.context.state_flags),
        allowed_next_event_types=_join_allowed_event_types(allowed_next_event_types),
    )
    