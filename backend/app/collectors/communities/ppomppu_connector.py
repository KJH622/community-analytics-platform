from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
import time
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.collectors.base.base import RequestPolicy
from app.collectors.base.types import NormalizedCommunityPost
from app.collectors.communities.base import BaseCommunityConnector


PPOMPPU_BASE_URL = "https://www.ppomppu.co.kr/zboard/"
PPOMPPU_HOME_URL = "https://www.ppomppu.co.kr/"
PPOMPPU_LIST_TEMPLATE = (
    "https://www.ppomppu.co.kr/zboard/zboard.php?id={board_id}&hotlist_flag=999&page={page}"
)
PPOMPPU_RECENT_TEMPLATE = "https://www.ppomppu.co.kr/zboard/zboard.php?id={board_id}&page={page}"


@dataclass(slots=True)
class PpomppuBoardConfig:
    board_id: str
    board_name: str
    community_name: str = "뽐뿌"
    page: int = 1
    max_pages: int = 160
    fallback_max_pages: int = 320
    target_days: int = 30
    daily_limit: int = 30


def _clean_text(node: Any) -> str | None:
    return node.get_text(" ", strip=True) if node else None


def _extract_numeric(value: str | None) -> int | None:
    if not value:
        return None
    matched = re.search(r"(\d[\d,]*)", value.replace(",", ""))
    return int(matched.group(1)) if matched else None


def _parse_recommend_pair(value: str | None) -> tuple[int | None, int | None]:
    if not value:
        return None, None
    matched = re.search(r"(\d+)\s*-\s*(\d+)", value)
    if not matched:
        single = _extract_numeric(value)
        return single, None
    return int(matched.group(1)), int(matched.group(2))


def _parse_ppomppu_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%y.%m.%d %H:%M:%S")
    except ValueError:
        return None


class PpomppuHotConnector(BaseCommunityConnector):
    collector_name = "ppomppu-hot-board"

    def __init__(self, config: PpomppuBoardConfig) -> None:
        super().__init__(
            policy=RequestPolicy(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
                ),
                timeout_seconds=25,
                retry_count=3,
                min_interval_seconds=0.35,
            )
        )
        self.config = config
        self._client: httpx.Client | None = None

    def fetch_board_metadata(self) -> dict[str, Any]:
        return {
            "community_name": self.config.community_name,
            "board_name": self.config.board_name,
            "board_id": self.config.board_id,
            "robots_note": "robots.txt allows /zboard/ paths for public forum listing and view pages.",
        }

    def fetch(self) -> Iterable[NormalizedCommunityPost]:
        daily_counts: dict[str, int] = defaultdict(int)
        posts: list[NormalizedCommunityPost] = []
        cutoff = datetime.now() - timedelta(days=max(self.config.target_days - 1, 0))
        seen_external_ids: set[str] = set()
        self._client = httpx.Client(
            headers={
                "User-Agent": self.policy.user_agent,
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
                "Referer": PPOMPPU_HOME_URL,
            },
            follow_redirects=True,
            timeout=self.policy.timeout_seconds,
        )
        try:
            # Prime cookies before board access.
            self._get(PPOMPPU_HOME_URL)

            for hot_only in (True, False):
                for item in self._fetch_posts_page(hot_only=hot_only):
                    external_id = item["external_id"]
                    if external_id in seen_external_ids:
                        continue

                    published_at = item.get("published_at")
                    if published_at is None or published_at < cutoff:
                        continue

                    day_key = published_at.date().isoformat()
                    if daily_counts[day_key] >= self.config.daily_limit:
                        continue

                    try:
                        detail = self.fetch_post_detail(item)
                        parsed = self.parse_post(detail)
                    except httpx.HTTPError:
                        continue

                    posts.append(self.normalize_post(parsed))
                    daily_counts[day_key] += 1
                    seen_external_ids.add(external_id)

                    if self._daily_target_met(daily_counts):
                        break

                if self._daily_target_met(daily_counts):
                    break
        finally:
            self._client.close()
            self._client = None

        return posts

    def fetch_posts_page(self) -> Iterable[dict[str, Any]]:
        return self._fetch_posts_page(hot_only=True)

    def _fetch_posts_page(self, *, hot_only: bool) -> Iterable[dict[str, Any]]:
        if self._client is None:
            raise RuntimeError("Ppomppu connector client is not initialized")

        posts: list[dict[str, Any]] = []
        max_pages = self.config.max_pages if hot_only else self.config.fallback_max_pages
        template = PPOMPPU_LIST_TEMPLATE if hot_only else PPOMPPU_RECENT_TEMPLATE

        for page in range(self.config.page, self.config.page + max_pages):
            try:
                response = self._get(template.format(board_id=self.config.board_id, page=page))
                response.raise_for_status()
            except httpx.HTTPError:
                break
            html = response.content.decode("euc-kr", errors="replace")
            soup = BeautifulSoup(html, "html.parser")

            for row in soup.select("tr.baseList"):
                if row.get("id") == "topNotice" or row.select_one("#notice-icon"):
                    continue

                title_link = row.select_one("a.baseList-title")
                href = title_link.get("href") if title_link else None
                if not href or "view.php" not in href:
                    continue

                author_node = row.select_one("span.baseList-name")
                time_cell = row.select_one("td.baseList-space[title]")
                published_at = _parse_ppomppu_datetime(time_cell.get("title")) if time_cell else None
                upvotes, downvotes = _parse_recommend_pair(_clean_text(row.select_one("td.baseList-rec")))

                posts.append(
                    {
                        "external_id": parse_qs(urlparse(href).query).get("no", [href])[-1],
                        "title": _clean_text(title_link),
                        "url": urljoin(PPOMPPU_BASE_URL, href),
                        "author_identifier": _clean_text(author_node),
                        "published_at": published_at,
                        "view_count": _extract_numeric(_clean_text(row.select_one("td.baseList-views"))),
                        "upvotes": upvotes,
                        "downvotes": downvotes,
                        "comment_count": _extract_numeric(_clean_text(row.select_one("span.baseList-c"))),
                    }
                )

        return posts

    def fetch_post_detail(self, item: dict[str, Any]) -> dict[str, Any]:
        if self._client is None:
            raise RuntimeError("Ppomppu connector client is not initialized")
        response = self._get(item["url"])
        response.raise_for_status()
        return {
            "item": item,
            "html": response.content.decode("euc-kr", errors="replace"),
        }

    def parse_post(self, payload: dict[str, Any]) -> dict[str, Any]:
        soup = BeautifulSoup(payload["html"], "html.parser")
        item = payload["item"]
        body_node = soup.select_one(".han")
        body_text = body_node.get_text(" ", strip=True) if body_node else None

        return {
            "community_name": self.config.community_name,
            "board_name": self.config.board_name,
            "external_id": item["external_id"],
            "title": (soup.select_one("meta[property='og:title']") or {}).get("content", item["title"]),
            "body": body_text,
            "published_at": item["published_at"],
            "author_identifier": item["author_identifier"],
            "view_count": item["view_count"],
            "upvotes": item["upvotes"],
            "downvotes": item["downvotes"],
            "comment_count": item["comment_count"],
            "url": item["url"],
        }

    def normalize_post(self, payload: dict[str, Any]) -> NormalizedCommunityPost:
        return NormalizedCommunityPost(
            source_code=f"ppomppu_{self.config.board_id}_hot",
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

    def _daily_target_met(self, daily_counts: dict[str, int]) -> bool:
        eligible_days = [count for count in daily_counts.values() if count > 0]
        return len(eligible_days) >= self.config.target_days and all(
            count >= self.config.daily_limit for count in eligible_days
        )

    def _get(self, url: str) -> httpx.Response:
        if self._client is None:
            raise RuntimeError("Ppomppu connector client is not initialized")
        self._respect_rate_limit()
        response = self._client.get(url)
        self._last_request_at = time.monotonic()
        return response
