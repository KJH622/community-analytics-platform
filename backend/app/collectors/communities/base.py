from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

from app.collectors.base.base import BaseCollector
from app.collectors.base.types import NormalizedCommunityPost


class BaseCommunityConnector(BaseCollector, ABC):
    """
    Community crawlers must respect robots.txt, terms of service, and source-specific
    rate limits. If compliance is unclear, connectors should remain disabled.
    """

    @abstractmethod
    def fetch_board_metadata(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def fetch_posts_page(self) -> Iterable[Any]:
        raise NotImplementedError

    @abstractmethod
    def fetch_post_detail(self, item: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    def parse_post(self, payload: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    def normalize_post(self, payload: Any) -> NormalizedCommunityPost:
        raise NotImplementedError

    def fetch(self) -> Iterable[NormalizedCommunityPost]:
        posts: list[NormalizedCommunityPost] = []
        for item in self.fetch_posts_page():
            detail = self.fetch_post_detail(item)
            parsed = self.parse_post(detail)
            posts.append(self.normalize_post(parsed))
        return posts
