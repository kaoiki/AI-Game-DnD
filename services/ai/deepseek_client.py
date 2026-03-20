from typing import Any

from deepseek import DeepSeekClient

from core.deepseek_config import DeepSeekConfig


class DeepSeekProvider:
    """
    DeepSeek 官方 SDK 最小封装层。
    """

    def __init__(self, config: DeepSeekConfig | None = None) -> None:
        self.config = config or DeepSeekConfig.from_env()
        self.client = DeepSeekClient(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
        )

    def complete_prompt(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 600,
    ) -> str:
        messages: list[dict[str, str]] = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        last_error: Exception | None = None

        for attempt in range(2):
            try:
                response = self.client.chat_completion(
                    messages=messages,
                    model=self.config.model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return self._extract_text(response)
            except Exception as exc:
                last_error = exc
                if attempt == 1:
                    raise

        if last_error:
            raise last_error

        raise RuntimeError("DeepSeek request failed unexpectedly")

    def _extract_text(self, response: Any) -> str:
        if response is None:
            raise RuntimeError("DeepSeek response is empty")

        if isinstance(response, dict):
            try:
                content = response["choices"][0]["message"]["content"]
                if content is None:
                    raise RuntimeError("DeepSeek response content is empty")
                return str(content).strip()
            except Exception:
                return str(response)

        choices = getattr(response, "choices", None)
        if choices:
            first_choice = choices[0]
            message = getattr(first_choice, "message", None)
            if message is not None:
                content = getattr(message, "content", None)
                if content is not None:
                    return str(content).strip()

        return str(response).strip()

    def smoke_test(self) -> str:
        return self.complete_prompt(
            "请只回复：deepseek connected",
            temperature=0,
            max_tokens=32,
        )


if __name__ == "__main__":
    provider = DeepSeekProvider()
    print(provider.smoke_test())