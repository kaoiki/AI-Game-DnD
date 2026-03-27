def build_dnd_event_init_prompt(target_event: str) -> str:
    return f"""
你是一个短局 AI 叙事游戏的世界观初始化助手。

你的任务是：
为一次 DND 风格的短局冒险，生成 3 个初始化偏好字段。

本次目标事件倾向是：
{target_event}

要求：
1. 只输出一个合法 JSON 对象
2. 不要输出解释、前言、Markdown、代码块
3. 只允许输出以下 3 个字段：
   - tone_bias
   - theme_bias
   - npc_bias
4. 每个字段都必须是字符串
5. 输出内容使用中文
6. 三个字段之间要有明显搭配感，适合组成同一局故事
7. 生成的 slots 必须尽量符合目标事件倾向：
   - decision：更偏试探、选择、分岔、观察、交涉
   - combat：更偏压迫、危险、敌意、追击、暴怒
   - puzzle：更偏机关、遗迹、符文、试炼、解谜
8. 只生成 slots，不要输出 event
9. 不要输出重复、空泛或无意义内容

输出示例：
{{
  "tone_bias": "紧张冒险",
  "theme_bias": "大山寻宝",
  "npc_bias": "山神"
}}

现在开始，只输出 JSON。
""".strip()