import json

from core.llm_exceptions import LLMJsonParseError


def strip_code_fence(text: str) -> str:
    text = text.strip()

    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    return text.strip()


def extract_first_json_object(text: str) -> str:
    """
    从模型输出中提取第一个完整 JSON 对象。
    支持：
    - 纯 JSON
    - ```json ... ``` 包裹
    - JSON 前后带解释文字
    """
    cleaned = strip_code_fence(text)

    start = cleaned.find("{")
    if start == -1:
        raise LLMJsonParseError("No JSON object found in model output")

    depth = 0
    in_string = False
    escape = False

    for idx in range(start, len(cleaned)):
        ch = cleaned[idx]

        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return cleaned[start : idx + 1]

    raise LLMJsonParseError("Incomplete JSON object in model output")


def parse_json_object(text: str) -> dict:
    if not text or not text.strip():
        raise LLMJsonParseError("Model output is empty")

    json_str = extract_first_json_object(text)

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise LLMJsonParseError(f"Invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise LLMJsonParseError("Model output JSON must be an object")

    return data