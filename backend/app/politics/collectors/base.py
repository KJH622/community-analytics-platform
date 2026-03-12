from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PoliticalNormalizedPost:
    source_code: str
    community_name: str
    board_name: str | None
    external_post_id: str
    title: str
    body: str
    created_at: str
    view_count: int | None
    upvotes: int | None
    comment_count: int | None
    original_url: str
    raw_payload: dict


class BasePoliticalCommunityConnector(ABC):
    connector_name: str = "base_political_connector"
    enabled: bool = False
    compliance_note: str = (
        "Enable only after robots.txt, service terms, and legal review are completed."
    )

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
    def normalize_post(self, parsed: dict) -> PoliticalNormalizedPost:
        raise NotImplementedError
