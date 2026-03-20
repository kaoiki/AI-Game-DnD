import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-chat"
DEFAULT_TIMEOUT = 60


@dataclass(frozen=True)
class DeepSeekConfig:
    api_key: str
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    timeout: int = DEFAULT_TIMEOUT

    @classmethod
    def from_env(cls) -> "DeepSeekConfig":
        api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("Missing DEEPSEEK_API_KEY in .env")

        base_url = os.getenv("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL).strip()
        model = os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL).strip()

        timeout_raw = os.getenv("DEEPSEEK_TIMEOUT", str(DEFAULT_TIMEOUT)).strip()
        try:
            timeout = int(timeout_raw)
        except ValueError:
            timeout = DEFAULT_TIMEOUT

        return cls(
            api_key=api_key,
            base_url=base_url or DEFAULT_BASE_URL,
            model=model or DEFAULT_MODEL,
            timeout=timeout,
        )