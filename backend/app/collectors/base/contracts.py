from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

from app.core.config import get_settings


@dataclass
class CollectorResult:
    name: str
    records_processed: int = 0
    message: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class BaseCollector(ABC):
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = httpx.Client(
            timeout=self.settings.request_timeout_seconds,
            headers={"User-Agent": self.settings.default_user_agent},
        )

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def get(self, url: str, **kwargs) -> httpx.Response:
        response = self.client.get(url, **kwargs)
        response.raise_for_status()
        return response

    @abstractmethod
    def collect(self, db) -> CollectorResult:
        raise NotImplementedError
