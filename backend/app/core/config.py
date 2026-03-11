from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "market-signal-hub"
    app_env: Literal["local", "test", "production"] = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/market_signal_hub"
    scheduler_enabled: bool = True
    scheduler_timezone: str = "Asia/Seoul"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://0.0.0.0:3000",
        ]
    )
    default_user_agent: str = "market-signal-hub/0.1 (+https://example.local)"
    request_timeout_seconds: int = 20
    request_rate_limit_per_source: float = 1.0
    community_max_pages_per_board: int = 3
    community_max_posts_per_board: int = 40
    fred_api_key: str | None = None
    bank_of_korea_api_key: str | None = None
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    openai_timeout_seconds: int = 30
    seed_demo_data: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
