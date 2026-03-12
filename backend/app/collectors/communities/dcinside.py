from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.collectors.base.contracts import CollectorResult
from app.collectors.communities.base import BaseCommunityConnector, NormalizedCommunityPost
from app.models import CommunityPost, Source, SourceType
from app.services.text_processor import anonymize_author
from app.utils.text import clean_text

COUNT_RE = re.compile(r"(\d+)")
SEOUL = ZoneInfo("Asia/Seoul")


class DCInsideConnector(BaseCommunityConnector):
    connector_name = "dcinside"
    enabled = True
    base_url = "https://gall.dcinside.com"
    boards = [
        {
            "id": "stockus",
            "board_name": "stockus-concept",
            "list_url": "https://gall.dcinside.com/mgallery/board/lists/?id=stockus&exception_mode=recommend",
            "snapshot_file": "stockus_recommend.json",
        },
        {
            "id": "jusik",
            "board_name": "전자주식투자 마이너 갤러리",
            "list_url": "https://gall.dcinside.com/mgallery/board/lists/?id=jusik",
        },
        {
            "id": "kospi",
            "board_name": "코스피 마이너 갤러리",
            "list_url": "https://gall.dcinside.com/mgallery/board/lists/?id=kospi",
        },
    ]
    board_name_map = {board["id"]: board["board_name"] for board in boards}

    def __init__(self) -> None:
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                ),
                "Referer": "https://gall.dcinside.com/",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            }
        )
        self.snapshot_dir = Path(__file__).resolve().parents[4] / "dcinside_today_2026-03-11"

    def get(self, url: str, **kwargs):
        response = self.session.get(url, timeout=self.settings.request_timeout_seconds, **kwargs)
        response.raise_for_status()
        return response

    def fetch_board_metadata(self) -> dict:
        return {
            "source": self.connector_name,
            "boards": [
                {"id": board["id"], "board_name": board["board_name"], "list_url": board["list_url"]}
                for board in self.boards
            ],
        }

    def fetch_posts_page(self, board: dict[str, str], page: int = 1) -> list[dict]:
        response = self.get(f"{board['list_url']}&page={page}")
        soup = BeautifulSoup(response.text, "html.parser")
        stubs: list[dict] = []

        for row in soup.select("tr.ub-content"):
            if row.get("data-type") == "icon_notice":
                continue

            subject = self._safe_text(row.select_one("td.gall_subject"))
            if subject in {"공지", "설문", "AD"}:
                continue

            post_no = self._safe_text(row.select_one("td.gall_num"))
            title_node = row.select_one("td.gall_tit a:not(.reply_numbox)")
            date_node = row.select_one("td.gall_date")
            writer_node = row.select_one("td.gall_writer")
            if not post_no or not post_no.isdigit() or not title_node or not date_node or not writer_node:
                continue

            href = title_node.get("href")
            if not href:
                continue

            stubs.append(
                {
                    "board_id": board["id"],
                    "board_name": board["board_name"],
                    "external_post_id": f"{board['id']}:{post_no}",
                    "post_no": post_no,
                    "title": self._safe_text(title_node),
                    "post_url": urljoin(self.base_url, href),
                    "created_at": date_node.get("title"),
                    "author": self._extract_author(writer_node),
                    "view_count": self._parse_int(self._safe_text(row.select_one("td.gall_count"))),
                    "upvotes": self._parse_int(self._safe_text(row.select_one("td.gall_recommend"))),
                    "comment_count": self._parse_comment_count(row),
                    "raw_row_text": row.get_text(" ", strip=True),
                }
            )

        if not stubs:
            return self._load_snapshot_posts(board, page)
        return stubs

    def fetch_post_detail(self, post_stub: dict[str, Any]) -> dict[str, Any]:
        response = self.get(post_stub["post_url"])
        soup = BeautifulSoup(response.text, "html.parser")

        detail = dict(post_stub)
        detail_body = self._safe_text(soup.select_one("div.write_div"))
        detail.update(
            {
                "title": self._safe_text(soup.select_one("span.title_subject")) or post_stub["title"],
                "body": clean_text(detail_body),
                "created_at": (soup.select_one("span.gall_date") or {}).get("title") or post_stub["created_at"],
                "view_count": self._parse_int(self._safe_text(soup.select_one("span.gall_count")))
                or post_stub.get("view_count"),
                "upvotes": self._parse_int(self._safe_text(soup.select_one("span.gall_reply_num")))
                or post_stub.get("upvotes"),
            }
        )
        detail["raw_detail_excerpt"] = detail_body[:500]
        return detail

    def parse_post(self, payload: dict[str, Any]) -> dict[str, Any]:
        return payload

    def normalize_post(self, parsed: dict[str, Any]) -> NormalizedCommunityPost:
        created_at = parsed.get("created_at")
        if not created_at:
            created_at = datetime.now(tz=timezone.utc).isoformat()

        parsed_created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        if parsed_created_at.tzinfo is None:
            parsed_created_at = parsed_created_at.replace(tzinfo=SEOUL)
        normalized_created_at = parsed_created_at.astimezone(timezone.utc)
        return NormalizedCommunityPost(
            board_name=parsed["board_name"],
            external_post_id=parsed["external_post_id"],
            title=clean_text(parsed["title"]),
            body=clean_text(parsed.get("body") or parsed["title"]),
            created_at=normalized_created_at.isoformat(),
            author_id=parsed.get("author"),
            view_count=parsed.get("view_count"),
            upvotes=parsed.get("upvotes"),
            downvotes=None,
            comment_count=parsed.get("comment_count"),
            original_url=parsed["post_url"],
            raw_payload=parsed,
        )

    def collect(self, db: Session) -> CollectorResult:
        return self.collect_live(db)

    def collect_live(
        self,
        db: Session,
        board_ids: list[str] | None = None,
        max_pages: int | None = None,
        max_posts: int | None = None,
    ) -> CollectorResult:
        source = db.execute(select(Source).where(Source.code == self.connector_name)).scalar_one_or_none()
        if source is None:
            source = Source(
                code=self.connector_name,
                name="DCInside Galleries",
                source_type=SourceType.COMMUNITY,
                country="KR",
                base_url=self.base_url,
                is_official=False,
                compliance_notes=(
                    "Public gallery pages only. Review robots.txt, site terms, and rate limits before scaling."
                ),
                metadata_json={"boards": self.fetch_board_metadata()["boards"]},
            )
            db.add(source)
            db.flush()

        processed = 0
        board_filter = set(board_ids or [])
        target_boards = [board for board in self.boards if not board_filter or board["id"] in board_filter]
        target_max_pages = max_pages or getattr(self.settings, "community_max_pages_per_board", 3)
        target_max_posts = max_posts or getattr(self.settings, "community_max_posts_per_board", 40)

        for board in target_boards:
            collected_for_board = 0
            for page in range(1, target_max_pages + 1):
                for stub in self.fetch_posts_page(board, page=page):
                    if collected_for_board >= target_max_posts:
                        break

                    exists = db.execute(
                        select(CommunityPost).where(
                            CommunityPost.source_id == source.id,
                            CommunityPost.external_post_id == stub["external_post_id"],
                        )
                    ).scalar_one_or_none()
                    if exists:
                        continue

                    detail = self.fetch_post_detail(stub)
                    normalized = self.normalize_post(self.parse_post(detail))

                    try:
                        db.add(
                            CommunityPost(
                                source_id=source.id,
                                board_name=normalized.board_name,
                                external_post_id=normalized.external_post_id,
                                title=normalized.title,
                                body=normalized.body,
                                created_at=datetime.fromisoformat(normalized.created_at),
                                author_hash=anonymize_author(normalized.author_id),
                                view_count=normalized.view_count,
                                upvotes=normalized.upvotes,
                                downvotes=normalized.downvotes,
                                comment_count=normalized.comment_count,
                                original_url=normalized.original_url,
                                raw_payload=normalized.raw_payload,
                            )
                        )
                        db.flush()
                    except IntegrityError:
                        db.rollback()
                        continue

                    processed += 1
                    collected_for_board += 1

                if collected_for_board >= target_max_posts:
                    break

        db.commit()
        return CollectorResult(
            name=self.connector_name,
            records_processed=processed,
            message=f"Stored {processed} DCInside posts across {len(target_boards)} galleries.",
        )

    def _load_snapshot_posts(self, board: dict[str, str], page: int) -> list[dict]:
        path = self.snapshot_dir / board.get("snapshot_file", f"{board['id']}.json")
        if not path.exists():
            return []

        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []

        page_size = 50
        start = (page - 1) * page_size
        end = start + page_size
        stubs: list[dict] = []
        for row in rows[start:end]:
            if row.get("gallery_id") != board["id"]:
                continue
            stubs.append(
                {
                    "board_id": board["id"],
                    "board_name": self.board_name_map.get(board["id"], board["board_name"]),
                    "external_post_id": f"{board['id']}:{row['post_no']}",
                    "post_no": str(row["post_no"]),
                    "title": row.get("title", ""),
                    "post_url": row.get("url", ""),
                    "created_at": row.get("datetime"),
                    "author": row.get("author"),
                    "view_count": None,
                    "upvotes": None,
                    "comment_count": None,
                    "raw_row_text": "",
                    "source_mode": "snapshot_fallback",
                }
            )
        return stubs

    @staticmethod
    def _safe_text(node: Any) -> str:
        if node is None:
            return ""
        return node.get_text(" ", strip=True)

    @staticmethod
    def _parse_int(value: str) -> int | None:
        match = COUNT_RE.search(value or "")
        if not match:
            return None
        return int(match.group(1))

    @staticmethod
    def _parse_comment_count(row: Any) -> int | None:
        reply_node = row.select_one("td.gall_tit a.reply_numbox")
        if reply_node is None:
            return None
        return DCInsideConnector._parse_int(reply_node.get_text(" ", strip=True))

    @staticmethod
    def _extract_author(node: Any) -> str:
        user_name = node.get("data-nick") or node.get("data-name")
        ip = node.get("data-ip")
        if user_name and ip:
            return f"{user_name} ({ip})"
        if user_name:
            return user_name
        return node.get_text(" ", strip=True)
