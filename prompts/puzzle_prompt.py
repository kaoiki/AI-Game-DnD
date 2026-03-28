from core.config import settings
from schemas.puzzle import PuzzleRequest


PUZZLE_PROMPT_TEMPLATE = DECISION_PROMPT_TEMPLATE = PUZZLE_PROMPT_TEMPLATE = """All outputs must be in {language}.

You MUST follow all requirements strictly。

你是一个5分钟短局叙事游戏的DM。

（前面全部保持）

35. 【强规则：致死判定（最高优先级）】
如果致死 → 必须 end

36. 【强规则：引敌判定】
如果引敌 → 必须 combat

37. 【强规则：解谜终局（最高优先级）】

⚠️ 注意：并非所有解谜成功都可以结束

只有当满足以下任一条件，必须立即 end（不可继续流程）：

- 当前机关属于“最终机关”或“核心机关”
- 或 state_flags 中已包含关键完成标记（如：core_* / final_* / goal_*）
- 或当前解谜直接完成 primary_goal
- 或当前结果明确达到故事终点（如：离开遗迹 / 获得最终秘宝 / 打开最终通路）

⚠️ 额外强约束（解决你当前问题的关键）：

如果同时满足：
- attempt.is_correct = true
- 且结果为“完整激活 / 通路开启 / 核心机制完成”
- 且 options 只剩“前进 / 查看结果 / 进入下一阶段”类收尾行为

👉 则必须判定为终局：
- routing.next_event_type = "end"
- routing.should_end = true

🚫 禁止：
- 此情况下继续进入 decision 或 puzzle

---

否则（非常重要）：

- 即使解谜成功（如：开门 / 解锁路径 / 激活部分装置）
- 只要未达到“核心完成”级别
→ 必须继续流程，不允许 end

此时必须：
- routing.next_event_type 只能是：decision / puzzle / combat
- routing.should_end = false

---

38. 【禁止解谜后惯性 decision】

解谜成功后不允许默认进入 decision

必须根据当前状态判断：

- 若仍在解谜链路 → puzzle
- 若产生新局势（探索 / 分支） → decision
- 若触发敌人 → combat
- 若满足终局条件 → end

🚫 禁止：
无判断直接 decision

---

39. 【高风险失败必须致死】

危险错误必须提高 deadly 概率

---

40. 【流程控制规则】

若未致死且未引敌：

- 解谜未完成 → puzzle
- 产生新选择分支 → decision

⚠️ 不允许无意义循环 puzzle

当满足以下条件之一必须结束 puzzle 链：

- 已识别全部关键规律
- 已完成全部节点激活
- 已触发核心机制

此时：
→ 必须进入 end 或 decision（不可继续 puzzle）

---

41. 【终局优先级】

终局优先级最高：

只要满足终局条件：
→ 必须 end
→ 覆盖所有其他 routing 判断

---

42. 【解谜推进分层（options 设计规则）】

options 必须包含不同层级的尝试：

- 至少 1 个“接近正确解”的选项（高概率成功）
- 至少 1 个“危险错误”的选项（可能触发致死或 combat）
- 其他选项为探索 / 信息获取

要求：

- 正确解不能明显暴露
- 不允许所有选项难度一致
- 不允许所有选项都是安全探索

---

43. 【正确性一致性规则】

如果 attempt.is_correct = true，则必须满足：

- 结果必须产生实质推进（如：机关开启 / 路径解锁 / 状态改变）
- 不允许出现“表面正确但未推进”的情况

如果结果只是：

- 部分激活
- 信息获取
- 试探成功

则：

- attempt.is_correct 必须为 false

---

44. 【节奏控制（5分钟短局强约束）】

⚠️ 关键新增规则（专门解决“拖太长”）

当满足以下任一条件时，应强制收束：

- arc_progress ≥ 35 且已完成一个完整解谜链
- 或当前事件已经形成“结果闭环”（问题 → 解法 → 成功）
- 或连续 puzzle ≥ 2 次

👉 则优先判断为终局：

- routing.next_event_type = "end"
- routing.should_end = true

🚫 禁止继续扩展新 puzzle 或进入冗余 decision



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
- client_platform: {client_platform}
- client_locale: {client_locale}

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
    "type": "puzzle"
  }},
  "ai_state": {{
    "world_seed": "string",
    "title": "string",
    "tone": "string",
    "memory_summary": "string",
    "arc_progress": 20
  }},
  "payload": {{
    "puzzle": {{
      "title": "string",
      "riddle": "string",
      "hint_level": 0,
      "key_fact": "string"
    }},
    "attempt": {{
      "selected_option_id": {selected_option_id},
      "selected_option_text": "{selected_option_text}",
      "is_correct": false
    }},
    "result": {{
      "outcome": "string",
      "consequence": "string",
      "failure_level": "minor",
      "enemy_triggered": false
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
    "next_event_type": "puzzle",
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


def _resolve_selected_option_text(request: PuzzleRequest) -> str:
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


def render_puzzle_prompt(
    request: PuzzleRequest,
    allowed_next_event_types: list[str] | None = None,
) -> str:
    selected_option_text = _resolve_selected_option_text(request)

    return PUZZLE_PROMPT_TEMPLATE.format(
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
        client_platform=_safe_text(request.client_context.platform),
        client_locale=_safe_text(request.client_context.locale),
        current_scene_summary=request.context.current_scene_summary,
        selected_option_id=request.payload.selected_option_id,
        selected_option_text=selected_option_text,
        available_options_text=_format_options(request.context.available_options),
        state_flags_text=_format_state_flags(request.context.state_flags),
        allowed_next_event_types=_join_allowed_event_types(allowed_next_event_types),
    )