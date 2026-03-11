from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Any


@dataclass(slots=True)
class NormalizedIndicator:
    code: str
    name: str
    country: str
    category: str
    unit: str | None
    frequency: str | None
    description: str | None
    source_url: str | None
    next_release_at: str | None = None


@dataclass(slots=True)
class NormalizedIndicatorRelease:
    indicator: NormalizedIndicator
    release_date: date
    release_time: time | None
    actual_value: float | None
    forecast_value: float | None
    previous_value: float | None
    unit: str | None
    importance: int
    country: str
    source_url: str | None


@dataclass(slots=True)
class NormalizedArticle:
    source_code: str
    title: str
    summary: str | None
    body: str | None
    author: str | None
    published_at: datetime | None
    canonical_url: str
    url: str
    category: str | None
    tags: list[str] | None = None
    raw_payload: dict[str, Any] | None = None


@dataclass(slots=True)
class NormalizedCommunityComment:
    external_id: str
    body: str
    published_at: datetime | None
    author_identifier: str | None
    upvotes: int | None
    downvotes: int | None
    raw_payload: dict[str, Any] | None = None


@dataclass(slots=True)
class NormalizedCommunityPost:
    source_code: str
    board_name: str
    external_id: str
    title: str
    body: str | None
    published_at: datetime | None
    author_identifier: str | None
    view_count: int | None
    upvotes: int | None
    downvotes: int | None
    comment_count: int | None
    url: str
    raw_payload: dict[str, Any] | None = None
    comments: list[NormalizedCommunityComment] = field(default_factory=list)
