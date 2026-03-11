from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "market-signal-hub"
    app_env: Literal["local", "test", "production"] = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    database_url: str = "sqlite:///./community_analytics.db"
    scheduler_enabled: bool = True
    scheduler_timezone: str = "Asia/Seoul"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )
    default_user_agent: str = "market-signal-hub/0.1 (+https://example.local)"
    request_timeout_seconds: int = 20
    request_rate_limit_per_source: float = 1.0
    community_request_interval_seconds: float = 1.0
    community_backfill_request_interval_seconds: float = 1.75
    community_request_jitter_seconds: float = 0.2
    community_max_pages_per_board: int = 3
    community_max_posts_per_board: int = 40
    community_incremental_pages_per_board: int = 3
    community_history_days: int = 30
    community_history_max_pages_per_board: int = 800
    fred_api_key: str | None = None
    bank_of_korea_api_key: str | None = None
    openai_api_key: str | None = None
    seed_demo_data: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
