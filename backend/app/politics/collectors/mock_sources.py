from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from dateutil import parser

from app.politics.collectors.base import (
    BasePoliticalCommunityConnector,
    NormalizedPoliticalIndicatorValue,
    NormalizedPoliticalPost,
)


class MockPoliticalCommunityConnector(BasePoliticalCommunityConnector):
    collector_name = "mock-political-community"

    def __init__(self, fixture_path: str | None = None) -> None:
        super().__init__()
        self.fixture_path = fixture_path or str(
            Path(__file__).resolve().parents[1] / "fixtures" / "political_posts.json"
        )

    def fetch_posts(self) -> Iterable[NormalizedPoliticalPost]:
        with open(self.fixture_path, "r", encoding="utf-8") as file:
            payload = json.load(file)
        return [
            NormalizedPoliticalPost(
                source_code="politics_mock",
                community_name=item["community_name"],
                board_name=item["board_name"],
                external_id=item["external_id"],
                title=item["title"],
                body=item.get("body"),
                published_at=_parse_datetime(item.get("published_at")),
                view_count=item.get("view_count"),
                upvotes=item.get("upvotes"),
                comment_count=item.get("comment_count"),
                url=item["url"],
                raw_payload=item,
            )
            for item in payload["posts"]
        ]


class MockPoliticalIndicatorCollector:
    def __init__(self, fixture_path: str | None = None) -> None:
        self.fixture_path = fixture_path or str(
            Path(__file__).resolve().parents[1] / "fixtures" / "political_indicators.json"
        )

    def fetch(self) -> list[NormalizedPoliticalIndicatorValue]:
        with open(self.fixture_path, "r", encoding="utf-8") as file:
            payload = json.load(file)
        return [
            NormalizedPoliticalIndicatorValue(
                indicator_code=item["indicator_code"],
                indicator_name=item["indicator_name"],
                country=item.get("country", "KR"),
                date=parser.isoparse(item["date"]).date(),
                value=float(item["value"]),
                source=item["source"],
                unit=item.get("unit", "%"),
                label=item.get("label"),
                description=item.get("description"),
            )
            for item in payload["values"]
        ]


def _parse_datetime(value: str | None) -> datetime | None:
    return parser.isoparse(value) if value else None
