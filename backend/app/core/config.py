from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="market-signal-hub", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    default_timezone: str = Field(default="Asia/Seoul", alias="DEFAULT_TIMEZONE")

    database_url: str = Field(
        default="sqlite+pysqlite:///./market_signal_hub.db", alias="DATABASE_URL"
    )
    async_database_url: str = Field(
        default="sqlite+aiosqlite:///./market_signal_hub.db", alias="ASYNC_DATABASE_URL"
    )

    request_timeout_seconds: int = Field(default=20, alias="REQUEST_TIMEOUT_SECONDS")
    http_user_agent: str = Field(default="market-signal-hub/0.1", alias="HTTP_USER_AGENT")

    bls_api_url: str = Field(
        default="https://api.bls.gov/publicAPI/v2/timeseries/data/",
        alias="BLS_API_URL",
    )
    fred_series_base_url: str = Field(
        default="https://fred.stlouisfed.org/graph/fredgraph.csv",
        alias="FRED_SERIES_BASE_URL",
    )
    nasdaq_markets_rss: str = Field(
        default="https://www.nasdaq.com/feed/rssoutbound?category=Markets",
        alias="NASDAQ_MARKETS_RSS",
    )
    nasdaq_stocks_rss: str = Field(
        default="https://www.nasdaq.com/feed/rssoutbound?category=Stocks",
        alias="NASDAQ_STOCKS_RSS",
    )

    community_connectors_enabled: bool = Field(
        default=False, alias="COMMUNITY_CONNECTORS_ENABLED"
    )
    mock_community_connector_enabled: bool = Field(
        default=True, alias="MOCK_COMMUNITY_CONNECTOR_ENABLED"
    )
    scheduler_enabled: bool = Field(default=True, alias="SCHEDULER_ENABLED")

    frontend_api_base_url: str = Field(
        default="http://localhost:8000", alias="FRONTEND_API_BASE_URL"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
