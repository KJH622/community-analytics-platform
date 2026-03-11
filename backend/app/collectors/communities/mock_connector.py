from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

from dateutil import parser

from app.collectors.base.types import NormalizedCommunityComment, NormalizedCommunityPost
from app.collectors.communities.base import BaseCommunityConnector


class MockCommunityConnector(BaseCommunityConnector):
    collector_name = "mock-community"

    def __init__(self, fixture_path: str | None = None) -> None:
        super().__init__()
        self.fixture_path = fixture_path or str(
            Path(__file__).resolve().parents[2] / "fixtures" / "community" / "mock_posts.json"
        )

    def fetch_board_metadata(self) -> dict[str, Any]:
        return {
            "name": "mock-invest-board",
            "note": "Safe local fixture connector for development and tests.",
        }

    def fetch_posts_page(self) -> Iterable[dict[str, Any]]:
        with open(self.fixture_path, "r", encoding="utf-8") as file:
            payload = json.load(file)
        return payload["posts"]

    def fetch_post_detail(self, item: dict[str, Any]) -> dict[str, Any]:
        return item

    def parse_post(self, payload: dict[str, Any]) -> dict[str, Any]:
        return payload

    def normalize_post(self, payload: dict[str, Any]) -> NormalizedCommunityPost:
        comments = [
            NormalizedCommunityComment(
                external_id=comment["external_id"],
                body=comment["body"],
                published_at=_parse_datetime(comment.get("published_at")),
                author_identifier=comment.get("author_identifier"),
                upvotes=comment.get("upvotes"),
                downvotes=comment.get("downvotes"),
                raw_payload=comment,
            )
            for comment in payload.get("comments", [])
        ]
        return NormalizedCommunityPost(
            source_code="mock_community",
            board_name=payload["board_name"],
            external_id=payload["external_id"],
            title=payload["title"],
            body=payload.get("body"),
            published_at=_parse_datetime(payload.get("published_at")),
            author_identifier=payload.get("author_identifier"),
            view_count=payload.get("view_count"),
            upvotes=payload.get("upvotes"),
            downvotes=payload.get("downvotes"),
            comment_count=payload.get("comment_count"),
            url=payload["url"],
            raw_payload=payload,
            comments=comments,
        )


def _parse_datetime(value: str | None) -> datetime | None:
    return parser.isoparse(value) if value else None
