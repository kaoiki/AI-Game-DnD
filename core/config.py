# from functools import lru_cache

# from pydantic import Field
# from pydantic_settings import BaseSettings, SettingsConfigDict


# class Settings(BaseSettings):
#     """
#     Application settings loaded from environment variables or .env file.
#     """

#     model_config = SettingsConfigDict(
#         env_file=".env",
#         env_file_encoding="utf-8",
#         extra="ignore",
#         case_sensitive=False,
#     )

#     # App
#     app_name: str = Field(default="LLM Event MVP")
#     app_version: str = Field(default="0.1.0")
#     debug: bool = Field(default=False)

#     # Server
#     host: str = Field(default="127.0.0.1")
#     port: int = Field(default=8000)

#     # Logging
#     log_level: str = Field(default="INFO")

#     # Database
#     duckdb_path: str = Field(default="data/app.duckdb")

#     # LLM
#     deepseek_api_key: str = Field(default="")
#     deepseek_api_url: str = Field(default="https://api.deepseek.cn/v1/chat/completions")
#     deepseek_base_url: str = Field(default="https://api.deepseek.com/v1")
#     deepseek_model: str = Field(default="deepseek-chat")
#     deepseek_timeout: int = Field(default=60)

#     # Event routing config
#     init_allowed_next_events_raw: str = Field(
#         default="decision,combat,puzzle"
#     )
#     loop_allowed_next_events_raw: str = Field(
#         default="decision,combat,puzzle,end"
#     )

#     @staticmethod
#     def _parse_event_csv(raw: str, fallback: list[str]) -> list[str]:
#         values: list[str] = []
#         for item in raw.split(","):
#             value = item.strip().lower()
#             if value and value not in values:
#                 values.append(value)
#         return values or fallback

#     @property
#     def init_allowed_next_events(self) -> list[str]:
#         return self._parse_event_csv(
#             self.init_allowed_next_events_raw,
#             ["decision", "combat", "puzzle"],
#         )

#     @property
#     def loop_allowed_next_events(self) -> list[str]:
#         return self._parse_event_csv(
#             self.loop_allowed_next_events_raw,
#             ["decision", "combat", "puzzle", "end"],
#         )


# @lru_cache
# def get_settings() -> Settings:
#     """
#     Return a cached Settings instance.
#     """
#     return Settings()


# settings = get_settings()

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # App
    app_name: str = Field(default="LLM Event MVP")
    app_version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)

    # Server
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)

    # Logging
    log_level: str = Field(default="INFO")

    # Database
    duckdb_path: str = Field(default="data/app.duckdb")

    # LLM
    deepseek_api_key: str = Field(default="")
    deepseek_api_url: str = Field(default="https://api.deepseek.cn/v1/chat/completions")
    deepseek_base_url: str = Field(default="https://api.deepseek.com/v1")
    deepseek_model: str = Field(default="deepseek-chat")
    deepseek_timeout: int = Field(default=60)

    # Event routing config
    init_allowed_next_events_raw: str = Field(
        default="decision,combat,puzzle"
    )
    loop_allowed_next_events_raw: str = Field(
        default="decision,combat,puzzle,end"
    )
    event_init_random_events_raw: str = Field(
        default="decision,combat,puzzle"
    )

    @staticmethod
    def _parse_event_csv(raw: str, fallback: list[str]) -> list[str]:
        values: list[str] = []
        for item in raw.split(","):
            value = item.strip().lower()
            if value and value not in values:
                values.append(value)
        return values or fallback

    @property
    def init_allowed_next_events(self) -> list[str]:
        return self._parse_event_csv(
            self.init_allowed_next_events_raw,
            ["decision", "combat", "puzzle"],
        )

    @property
    def loop_allowed_next_events(self) -> list[str]:
        return self._parse_event_csv(
            self.loop_allowed_next_events_raw,
            ["decision", "combat", "puzzle", "end"],
        )

    @property
    def event_init_random_events(self) -> list[str]:
        return self._parse_event_csv(
            self.event_init_random_events_raw,
            ["decision", "combat", "puzzle"],
        )


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings instance.
    """
    return Settings()


settings = get_settings()