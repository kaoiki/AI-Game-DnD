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


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings instance.
    """
    return Settings()


settings = get_settings()