from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.collectors.base.contracts import BaseCollector, CollectorResult


@dataclass
class NormalizedCommunityPost:
    board_code: str | None
    board_name: str
    topic_category: str | None
    external_post_id: str
    title: str
    body: str
    created_at: str
    author_id: str | None
    view_count: int | None
    upvotes: int | None
    downvotes: int | None
    comment_count: int | None
    original_url: str
    raw_payload: dict


class BaseCommunityConnector(BaseCollector, ABC):
    connector_name: str = "base_community"
    enabled: bool = False
    compliance_note: str = (
        "Check robots.txt, site terms, legal restrictions, and rate limits before enabling live crawling."
    )

    @abstractmethod
    def fetch_board_metadata(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def fetch_posts_page(self) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def fetch_post_detail(self, post_stub: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def parse_post(self, payload: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def normalize_post(self, parsed: dict) -> NormalizedCommunityPost:
        raise NotImplementedError

    def collect(self, db) -> CollectorResult:
        raise NotImplementedError
