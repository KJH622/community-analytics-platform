from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from app.collectors.base.base import BaseCollector


@dataclass(slots=True)
class NormalizedPoliticalPost:
    source_code: str
    community_name: str
    board_name: str
    external_id: str
    title: str
    body: str | None
    published_at: datetime | None
    view_count: int | None
    upvotes: int | None
    comment_count: int | None
    url: str
    raw_payload: dict[str, Any] | None = None


@dataclass(slots=True)
class NormalizedPoliticalIndicatorValue:
    indicator_code: str
    indicator_name: str
    country: str
    date: date
    value: float
    source: str
    unit: str
    label: str | None = None
    description: str | None = None


class BasePoliticalCommunityConnector(BaseCollector, ABC):
    @abstractmethod
    def fetch_posts(self) -> Iterable[NormalizedPoliticalPost]:
        raise NotImplementedError

    def fetch(self) -> Iterable[NormalizedPoliticalPost]:
        return self.fetch_posts()
