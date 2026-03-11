from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.collectors.base.exceptions import CollectorError
from app.core.config import get_settings


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RequestPolicy:
    user_agent: str
    timeout_seconds: int
    retry_count: int = 3
    min_interval_seconds: float = 0.5


class BaseCollector(ABC):
    collector_name = "base"

    def __init__(self, policy: RequestPolicy | None = None) -> None:
        settings = get_settings()
        self.policy = policy or RequestPolicy(
            user_agent=settings.http_user_agent,
            timeout_seconds=settings.request_timeout_seconds,
        )
        self._last_request_at = 0.0

    def _headers(self) -> dict[str, str]:
        return {"User-Agent": self.policy.user_agent}

    def _respect_rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        wait_time = max(0.0, self.policy.min_interval_seconds - elapsed)
        if wait_time:
            time.sleep(wait_time)

    @retry(
        retry=retry_if_exception_type(httpx.HTTPError),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def get_json(self, url: str, **kwargs: Any) -> Any:
        self._respect_rate_limit()
        with httpx.Client(timeout=self.policy.timeout_seconds, headers=self._headers()) as client:
            response = client.get(url, **kwargs)
            response.raise_for_status()
            self._last_request_at = time.monotonic()
            return response.json()

    @retry(
        retry=retry_if_exception_type(httpx.HTTPError),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def get_text(self, url: str, **kwargs: Any) -> str:
        self._respect_rate_limit()
        with httpx.Client(timeout=self.policy.timeout_seconds, headers=self._headers()) as client:
            response = client.get(url, **kwargs)
            response.raise_for_status()
            self._last_request_at = time.monotonic()
            return response.text

    @abstractmethod
    def fetch(self) -> Iterable[Any]:
        raise NotImplementedError

    def safe_fetch(self) -> Iterable[Any]:
        try:
            return list(self.fetch())
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Collector failed: %s", self.collector_name)
            raise CollectorError(str(exc)) from exc
