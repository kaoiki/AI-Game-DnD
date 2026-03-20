class LLMOutputError(Exception):
    """LLM 输出相关异常基类。"""


class LLMEmptyResponseError(LLMOutputError):
    """LLM 返回为空。"""


class LLMJsonParseError(LLMOutputError):
    """LLM 返回无法解析为合法 JSON。"""


class LLMSchemaValidationError(LLMOutputError):
    """LLM 返回 JSON 结构不符合 schema。"""


class LLMInvokeError(LLMOutputError):
    """LLM 调用过程失败。"""