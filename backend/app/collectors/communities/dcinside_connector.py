from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup
from dateutil import parser

from app.collectors.base.base import RequestPolicy
from app.collectors.base.types import NormalizedCommunityPost
from app.collectors.communities.base import BaseCommunityConnector


DC_BASE_URL = "https://gall.dcinside.com"
LIST_URL_TEMPLATE = "https://gall.dcinside.com/mgallery/board/lists/?id={gallery_id}&page={page}"


@dataclass(slots=True)
class DcInsideGalleryConfig:
    gallery_id: str
    board_name: str
    community_name: str = "디시인사이드"
    page: int = 1
    max_pages: int = 1
    limit: int = 12


def extract_numeric(value: str | None) -> int | None:
    if not value:
        return None
    matched = re.search(r"(\d[\d,]*)", value.replace(",", ""))
    return int(matched.group(1)) if matched else None


def parse_dcinside_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return parser.parse(value)
    except Exception:
        return None


def resolve_dcinside_url(href: str) -> str:
    return urljoin(DC_BASE_URL, href)


def extract_post_id(href: str) -> str:
    query = parse_qs(urlparse(href).query)
    return query.get("no", [href])[-1]


class DcInsideConnector(BaseCommunityConnector):
    collector_name = "dcinside-gallery"

    def __init__(self, config: DcInsideGalleryConfig) -> None:
        super().__init__(
            policy=RequestPolicy(
                user_agent="market-signal-hub/0.1 (+public-data-crawler)",
                timeout_seconds=20,
                retry_count=3,
                min_interval_seconds=1.2,
            )
        )
        self.config = config

    def fetch_board_metadata(self) -> dict[str, Any]:
        return {
            "community_name": self.config.community_name,
            "board_name": self.config.board_name,
            "gallery_id": self.config.gallery_id,
            "robots_note": "Use only public list/view pages that are not disallowed in robots.txt.",
        }

    def fetch_posts_page(self) -> Iterable[dict[str, Any]]:
        posts: list[dict[str, Any]] = []

        for page in range(self.config.page, self.config.page + self.config.max_pages):
            html = self.get_text(LIST_URL_TEMPLATE.format(gallery_id=self.config.gallery_id, page=page))
            soup = BeautifulSoup(html, "html.parser")

            for row in soup.select("tr.ub-content"):
                kind = _text(row.select_one("td.gall_num"))
                title_link = row.select_one("td.gall_tit a")
                href = title_link.get("href") if title_link else None
                if not href:
                    continue
                if kind in {"공지", "AD", "설문"}:
                    continue
                if href.startswith("javascript:") or "addc.dcinside.com" in href:
                    continue

                posts.append(
                    {
                        "external_id": extract_post_id(href),
                        "title": _text(title_link),
                        "url": resolve_dcinside_url(href),
                        "author_identifier": _text(row.select_one("td.gall_writer")),
                        "list_date": _text(row.select_one("td.gall_date")),
                        "list_view_count": extract_numeric(_text(row.select_one("td.gall_count"))),
                        "list_upvotes": extract_numeric(_text(row.select_one("td.gall_recommend"))),
                    }
                )
                if len(posts) >= self.config.limit:
                    return posts

        return posts

    def fetch_post_detail(self, item: dict[str, Any]) -> dict[str, Any]:
        html = self.get_text(item["url"])
        return {"item": item, "html": html}

    def parse_post(self, payload: dict[str, Any]) -> dict[str, Any]:
        soup = BeautifulSoup(payload["html"], "html.parser")
        item = payload["item"]
        body_node = soup.select_one("div.write_div")

        return {
            "community_name": self.config.community_name,
            "board_name": self.config.board_name,
            "external_id": item["external_id"],
            "title": _text(soup.select_one("span.title_subject")) or item["title"],
            "body": body_node.get_text(" ", strip=True) if body_node else None,
            "published_at": parse_dcinside_datetime(_text(soup.select_one("span.gall_date"))),
            "author_identifier": item["author_identifier"],
            "view_count": extract_numeric(_text(soup.select_one("span.gall_count"))) or item["list_view_count"],
            "upvotes": extract_numeric(_text(soup.select_one("span.gall_reply_num"))) or item["list_upvotes"],
            "downvotes": None,
            "comment_count": extract_numeric(_text(soup.select_one("span.gall_comment"))),
            "url": item["url"],
        }

    def normalize_post(self, payload: dict[str, Any]) -> NormalizedCommunityPost:
        return NormalizedCommunityPost(
            source_code=f"dcinside_{self.config.gallery_id}",
            board_name=payload["board_name"],
            external_id=payload["external_id"],
            title=payload["title"],
            body=payload["body"],
            published_at=payload["published_at"],
            author_identifier=payload["author_identifier"],
            view_count=payload["view_count"],
            upvotes=payload["upvotes"],
            downvotes=payload["downvotes"],
            comment_count=payload["comment_count"],
            url=payload["url"],
            raw_payload=payload,
        )


def _text(node: Any) -> str | None:
    return node.get_text(" ", strip=True) if node else None
