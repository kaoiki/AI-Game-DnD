from core.config import settings
from schemas.end import EndRequest


END_PROMPT_TEMPLATE = """All outputs must be in {language}.

You MUST follow all requirements strictly.

你是一个5分钟短局叙事游戏的DM。

请根据给定输入，生成一次 END 事件结果。

END 的职责：
- 收束整局故事
- 输出最终结局
- 输出尾声场景
- 提炼本局关键选择
- 生成可供后续 NOVEL 接口直接使用的摘要

你只负责内容生成，不负责最终事件调度。
END 是终局事件，因此 routing 必须固定为结束态。

要求：
1. 只输出一个合法 JSON 对象
2. 不要输出解释、前言、Markdown、代码块
3. event.type 必须是 "end"（小写）
4. ai_state 必须包含：
   - world_seed
   - title
   - tone
   - memory_summary
   - arc_progress
5. arc_progress 必须大于等于 0，且应体现本局已经推进到终局
6. payload 必须包含：
   - ending
   - epilogue
   - key_choices
   - novel_summary
7. payload.ending 必须包含：
   - title
   - outcome
8. payload.epilogue 必须包含：
   - scene
   - closing_line
9. payload.key_choices 必须是数组
10. payload.key_choices 至少包含 1 项，最多不超过 5 项
11. payload.key_choices 的每一项必须包含：
   - event_type
   - choice_text
   - impact
12. payload.key_choices 中的 event_type 必须使用小写
13. payload.novel_summary 必须包含：
   - story_overview
   - player_journey
   - final_outcome
14. novel_summary 必须基于“整局历史事件”生成，不能只总结最后一个事件
15. novel_summary 必须覆盖：
   - 开局背景或主线目标
   - 中途关键推进
   - 玩家关键选择及其影响
   - 最终结局
16. payload 中禁止出现 options
17. END 不再提供下一轮玩家动作
18. context 必须包含：
   - current_scene_summary（字符串）
   - available_options（数组，END 必须为空数组）
   - state_flags（对象）
19. routing 必须包含：
   - next_event_type
   - should_end
20. routing.next_event_type 必须固定为 "end"
21. routing.should_end 必须固定为 true
22. meta 必须包含：
   - trace_id（字符串）
23. 所有文本字段（包括 title、memory_summary、outcome、scene、closing_line、impact、story_overview、player_journey、final_outcome 等）必须严格使用 language 指定的语言输出
24. 不得混用其他语言，必须保持语言一致性
25. 所有内容必须使用 language 指定的语言和语气表达
26. 输出必须为单一语言环境，不允许出现中文与非中文混合
27. 不要重写整个世界观，不要重新开新剧情，只总结并收束当前这一局
28. ending.title 应是本局结局名称，不要过长
29. ending.outcome 应清晰说明玩家最后达成了什么、失去了什么、改变了什么
30. epilogue.scene 应是结局落幕时的最终场景
31. epilogue.closing_line 应像结尾句，适合直接展示给玩家
32. key_choices 必须来自历史事件中的真实关键选择，不允许凭空捏造无关选择
33. key_choices 应优先提取对结局影响最大的选择，而不是流水账
34. novel_summary 的写法应适合后续 NOVEL 接口继续扩写成长文本
35. novel_summary 应更偏“可复述的故事摘要”，而不是抒情散文
36. current_scene_summary 必须是 epilogue.scene 的压缩承接版本
37. context.available_options 必须为空数组 []
38. 禁止出现 forbidden_terms 中的词
39. epilogue.scene 长度应尽量不超过 max_chars_scene
40. 若历史事件不足，也必须基于已有历史给出一个完整、可读、可扩写的终局总结
41. 历史事件中若存在玩家选择记录，必须尽量体现在 key_choices 和 novel_summary 中
42. 历史事件中若存在多个事件类型（如 init / decision / combat / puzzle），应体现它们对结局形成的链路
43. 不允许把 key_choices 写成纯结果；必须体现“玩家做了什么”
44. 不允许把 novel_summary 写成字段清单式短语；必须是连贯自然语言
45. 结局必须有明确收束感，不能写成“未完待续”或继续分支
46. 如果 history_events 中没有有效的 selected_option_text，则 key_choices 不得编造具体动作名称
47. 如果历史选择缺失，key_choices 和 novel_summary 只能概括为“做出推进、坚持面对、继续探索、推动局势发展”等抽象表达，不能伪造明确选项文本
48. novel_summary 必须优先使用“发生了什么 → 玩家做了什么或推动了什么 → 结果如何”的摘要式表达
49. novel_summary 不得过度使用抽象哲思、意识流、象征化表达，除非这些内容在历史事件中已有明确依据

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
- forbidden_terms: {forbidden_terms}
- tone_bias: {tone_bias}
- theme_bias: {theme_bias}
- npc_bias: {npc_bias}
- client_platform: {client_platform}
- client_locale: {client_locale}

当前状态输入：
- current_scene_summary: {current_scene_summary}
- state_flags:
{state_flags_text}

整局历史事件摘要（必须重点参考）：
{history_events_text}

输出示例结构：
{{
  "event": {{
    "type": "end"
  }},
  "ai_state": {{
    "world_seed": "string",
    "title": "string",
    "tone": "string",
    "memory_summary": "string",
    "arc_progress": 100
  }},
  "payload": {{
    "ending": {{
      "title": "string",
      "outcome": "string"
    }},
    "epilogue": {{
      "scene": "string",
      "closing_line": "string"
    }},
    "key_choices": [
      {{
        "event_type": "decision",
        "choice_text": "string",
        "impact": "string"
      }}
    ],
    "novel_summary": {{
      "story_overview": "string",
      "player_journey": "string",
      "final_outcome": "string"
    }}
  }},
  "routing": {{
    "next_event_type": "end",
    "should_end": true
  }},
  "context": {{
    "current_scene_summary": "string",
    "available_options": [],
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


def _format_state_flags(state_flags: dict) -> str:
    if not state_flags:
        return "{}"
    pairs = []
    for k, v in state_flags.items():
        pairs.append(f'- "{k}": {repr(v)}')
    return "\n".join(pairs)


def _format_history_events(history_events: list[dict] | None) -> str:
    if not history_events:
        return "- 无历史事件记录，请基于当前上下文生成一个完整终局总结"

    lines: list[str] = []
    for idx, item in enumerate(history_events, start=1):
        event_type = str(item.get("event_type", "unknown")).strip().lower() or "unknown"
        scene = str(item.get("scene_summary", "")).strip() or "无"
        choice = str(item.get("selected_option_text", "")).strip() or "无"
        result = str(item.get("result_summary", "")).strip() or "无"

        lines.append(
            f"{idx}. event_type={event_type} | "
            f"scene={scene} | "
            f"choice={choice} | "
            f"result={result}"
        )

    return "\n".join(lines)


def render_end_prompt(
    request: EndRequest,
    history_events: list[dict] | None = None,
) -> str:
    return END_PROMPT_TEMPLATE.format(
        hard_limit_seconds=request.time.hard_limit_seconds,
        elapsed_active_seconds=request.time.elapsed_active_seconds,
        remaining_seconds=request.time.remaining_seconds,
        difficulty=request.session.difficulty,
        player_count=request.session.player_count,
        run_seed=request.seed.run_seed,
        language=request.constraints.language,
        max_chars_scene=request.constraints.max_chars_scene,
        forbidden_terms=_join_terms(request.constraints.forbidden_terms),
        tone_bias=_safe_text(request.slots.tone_bias),
        theme_bias=_safe_text(request.slots.theme_bias),
        npc_bias=_safe_text(request.slots.npc_bias),
        client_platform=_safe_text(request.client_context.platform),
        client_locale=_safe_text(request.client_context.locale),
        current_scene_summary=request.context.current_scene_summary,
        state_flags_text=_format_state_flags(request.context.state_flags),
        history_events_text=_format_history_events(history_events),
    )