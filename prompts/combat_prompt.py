from core.config import settings
from schemas.combat import CombatRequest


COMBAT_PROMPT_TEMPLATE = COMBAT_PROMPT_TEMPLATE = """All outputs must be in {language}.

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

========================
【最高优先级规则（不可被覆盖）】
========================

如果满足任一条件，必须立即结束本局（优先级高于所有规则）：

1. 主要敌人被击杀 / 丧失行动能力
2. 核心目标已达成（例如：夺旗 / 逃脱 / 获取关键物品）
3. 当前冲突已失去继续战斗的意义
4. 玩家死亡

一旦触发：

- routing.next_event_type = "end"
- routing.should_end = true

并且必须遵守：

- ❌ 不允许生成新的敌人
- ❌ 不允许因为“还有其他人/威胁”继续 combat
- ❌ 不允许再进入 decision / puzzle
- ❌ 不允许生成新的战斗循环

（此规则优先级高于所有 routing / options 判断规则）

========================
基础要求
========================

1. 只输出一个合法 JSON 对象
2. 不要输出解释、前言、Markdown、代码块
3. event.type 必须是 "combat"（小写）

4. ai_state 必须包含：
   - world_seed
   - title
   - tone
   - memory_summary
   - arc_progress

5. arc_progress 必须大于等于 0，且必须体现推进

6. COMBAT 是单回合事件

7. payload 只包含：
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

11. option 必须包含：
   - id
   - text

12. context 必须包含：
   - current_scene_summary
   - available_options（必须与 payload.options 完全一致）
   - state_flags

13. routing 必须包含：
   - next_event_type（从 allowed_next_event_types 选择）
   - should_end（布尔值）

14. 如果 next_event_type = "end"，则 should_end = true
15. 否则 should_end = false

16. meta 必须包含 trace_id

17. 所有文本必须使用 language 指定语言
18. 禁止混用语言

========================
战斗逻辑
========================

19. 敌人名称不得来自输入
必须基于 current_scene_summary 生成统一敌人称呼

20. 回合结构必须是：
玩家动作 → 敌方反应 → 结果结算

21. 你必须判断：
- 玩家死亡
- 或玩家存活

如果玩家死亡：
→ 必须结束（触发最高优先级规则）

========================
终局强化规则（补充）
========================

22. 如果 outcome 表达以下语义之一：

- 击杀敌人
- 敌人瘫痪 / 无法行动
- 玩家已拿到核心目标（如战旗）

→ 必须结束（直接触发最高优先级规则）

23. 如果 arc_progress >= 80 且本回合是关键冲突：

→ 高概率结束（优先判断是否终局）

========================
战斗推进规则
========================

24. 不允许多回合“无进展战斗”

25. 每回合必须改变局势：
- 位置变化
- 状态变化
- 威胁变化

========================
routing 规则（仅在未终局时生效）
========================

⚠️ 仅当“未触发终局规则”时，以下规则才生效：

26. 根据 options 决定：

- 战斗行为 → combat
- 解谜行为 → puzzle
- 普通推进 → decision

========================
高风险规则
========================

27. 高风险行为必须可能致死：

例如：
- 贴身硬拼
- 强行突破
- 无防护攻击

→ 必须显著提高死亡概率

28. 不允许所有结果都是安全胜利

========================
options 设计规则
========================

29. options 必须包含：

- 至少1个推进关键局势
- 至少1个高风险行为
- 其他可为策略行为

30. 禁止写出“终结/最后一击”等明确提示

31. option.text 尽量不超过 max_option_chars

========================
context 规则
========================

32. current_scene_summary 必须是 scene.summary 的压缩版
33. available_options 必须一致

========================
限制
========================

34. 禁止重复 INIT 开场
35. 禁止生成无关剧情
36. 禁止出现 forbidden_terms
37. scene.summary 尽量不超过 max_scene_chars


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
    