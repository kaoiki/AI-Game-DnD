from core.config import settings
from schemas.puzzle import PuzzleRequest


PUZZLE_PROMPT_TEMPLATE = """All outputs must be in {language}.

You MUST follow all requirements strictly.

你是一个5分钟短局叙事游戏的DM。

请根据给定输入，生成一次 PUZZLE 事件结果。

PUZZLE 的职责：
- 承接玩家本次解谜选择
- 判断本次尝试是否正确
- 输出本次解谜结果
- 输出解谜后的新场景
- 给出新的 options
- 给出下一事件建议（routing）

你只负责内容生成，不负责最终事件调度。
routing.next_event_type 只是“建议”，不是最终控制权。

要求：
1. 只输出一个合法 JSON 对象
2. 不要输出解释、前言、Markdown、代码块
3. event.type 必须是 "puzzle"（小写）
4. ai_state 必须包含：
   - world_seed
   - title
   - tone
   - memory_summary
   - arc_progress
5. arc_progress 必须大于等于 0，且应体现剧情推进，不能倒退
6. payload 必须包含：
   - puzzle
   - attempt
   - result
   - scene
   - options
8. payload.puzzle 必须包含：
   - title
   - riddle
   - hint_level
   - key_fact
9. payload.attempt 必须包含：
   - selected_option_id
   - selected_option_text
   - is_correct
10. payload.result 必须包含：
   - outcome
   - consequence
   - failure_level
   - enemy_triggered
11. payload.result.failure_level 只能是：
   - "none"
   - "minor"
   - "major"
   - "deadly"
12. payload.scene 必须包含：
   - summary
   - npc_line
13. options 数量必须是 2 到 4 个
14. 每个 option 必须包含：
   - id（整数）
   - text（字符串）
15. context 必须包含：
   - current_scene_summary（字符串）
   - available_options（数组，内容必须与 payload.options 对齐）
   - state_flags（对象）
16. routing 必须包含：
   - next_event_type（只能从 allowed_next_event_types 中选择）
   - should_end（布尔值）
17. 如果 routing.next_event_type 是 "end"，则 should_end 必须为 true
18. 如果 routing.next_event_type 不是 "end"，则 should_end 必须为 false
19. meta 必须包含：
   - trace_id（字符串）
20. 所有文本字段（包括 title、memory_summary、riddle、key_fact、outcome、consequence、scene、npc_line、options 等）必须严格使用 language 指定的语言输出
21. 不得混用其他语言，必须保持语言一致性
22. 所有内容必须使用 language 指定的语言和语气表达
23. 输出必须为单一语言环境，不允许出现中文与非中文混合
24. payload.attempt.selected_option_id 必须等于输入中的 selected_option_id
25. payload.attempt.selected_option_text 必须与输入中 selected_option_id 对应的选项文本一致
26. PUZZLE 必须是真正的“解谜事件”，不能退化成普通剧情选择
27. 谜题必须带有迷惑性，不能过于简单，错误选项也必须看起来合理，不能一眼排除
28. 谜题的难度应来自场景线索、误导、机关逻辑、顺序判断、符号解释、条件组合，而不是纯冷知识
29. 选项必须都是“解谜尝试”或“与当前谜题后果直接相关的应对动作”，不能是空泛描述
30. 不允许生成无关选项，例如泛泛的“继续前进”“四处看看”“想一想”
31. payload.attempt.is_correct 必须明确反映本次选择是否正确
32. 如果玩家选对了，必须体现合理的正向推进，例如机关开启、线索解锁、危险缓解、路径打开
33. 如果玩家选错了，必须体现合理后果，例如机关误触、局势恶化、线索偏移、敌意增强、风险上升
34. 错误后果可以严重，但不能无意义；必须推动局面变化
35. 【强规则：致死判定（最高优先级）】
如果玩家的错误行为属于以下任一情况：
- 触发不可逆致命机关（坠落、贯穿、斩首、爆裂、毒杀）
- 明确导致角色死亡或完全失去行动能力
- 无任何补救空间的失败

则必须：
- payload.result.failure_level = "deadly"
- routing.next_event_type = "end"
- routing.should_end = true

❗禁止将致死结果降级为 "major" 或 "minor"

36. 【强规则：引敌判定（第二优先级）】
如果玩家的行为导致以下任一情况，必须判定为引敌：
- 惊动守卫、石像、巡逻者、怪物、咒灵、活化机关
- 敌人已经出现、现身、苏醒、逼近、锁定玩家、开始追击
- 场景已经从“解谜”转入“对抗 / 应战 / 逃生中的战斗状态”
- 明确出现了可被视为敌对单位的存在，而不只是环境异响

则必须：
- payload.result.enemy_triggered = true
- payload.result.failure_level 不能为 "none" 或 "minor"，至少为 "major"
- routing.next_event_type = "combat"
- routing.should_end = false

以下情况也必须视为引敌，而不是普通 suspense：
- 守卫从沉睡中苏醒
- 石像开始活动并朝玩家转向
- 咒灵、怪物、敌对生物被唤醒或召来
- 敌对目标已经进入当前场景或下一秒即可接战

❗禁止把“敌人已经出现 / 苏醒 / 逼近 / 锁定玩家”写成 enemy_triggered = false
❗禁止把“明确引敌”写成 next_event_type = "puzzle" 或 "decision"

37. 【禁止模糊处理】
- 不允许把明确致死写成普通失败
- 不允许把明确引敌写成普通推进
- 不允许使用“似乎惊动了什么”“仿佛有东西醒来”“远处传来声响”来回避 enemy_triggered 判定
- 只要敌对存在已经被唤醒、出现、逼近或即将交战，就必须归类为 combat
- 必须做出清晰分类（deadly / combat / normal）

38. 【优先级规则】
- deadly 优先级 > enemy_triggered > normal
- 若同时发生致死与引敌，以 deadly 为准（直接 end）
- 若未致死，但敌对目标已经出现、苏醒、逼近或锁定玩家，则必须进入 combat
- 只有在“尚未引敌、尚未致死、且主要玩法仍是继续破解机关”时，才允许返回 puzzle
39. 除了“deadly -> end”和“enemy_triggered -> combat”这两种强语义情况外，其余情况下 routing.next_event_type 才根据当前结果和下一步玩法建议为 decision / puzzle / combat / end
40. 不要因为出现“符文”“机关”“试炼”等词，就机械输出 "puzzle"
41. routing 必须反映“这一轮解谜结算后，下一步主要玩法是什么”
42. 如果谜题尚未解完，且下一步仍主要围绕继续破解规则、判断顺序、解读线索、尝试机关，则建议 next_event_type 为 "puzzle"
43. 如果谜题已解开，接下来主要是普通推进、探索、交流、处理结果，则建议 next_event_type 为 "decision"
44. 如果错误导致敌人出现或进入对抗，则建议 next_event_type 为 "combat"
45. 只有形成终局时，才建议 next_event_type 为 "end"
46. 同一谜题中，不同选择导向不同 next_event_type，是合理的
47. context.current_scene_summary 必须是 scene.summary 的压缩承接版本
48. context.available_options 必须与 payload.options 一致
49. 不要重写整个世界观，不要重复 INIT 开场，只推进当前局面
50. 禁止出现 forbidden_terms 中的词
51. option.text 长度应尽量不超过 max_option_chars
52. scene.summary 长度应尽量不超过 max_scene_chars

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