from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.collectors.base.contracts import CollectorResult
from app.collectors.communities.base import BaseCommunityConnector, NormalizedCommunityPost
from app.models import CommunityPost, Source, SourceType
from app.services.community_analysis import CommunityAnalysisService
from app.services.text_processor import anonymize_author
from app.utils.text import clean_text

COUNT_RE = re.compile(r"(\d+)")
HANGUL_RE = re.compile(r"[가-힣]")
MOJIBAKE_RE = re.compile(r"[一-龥ぁ-ゟ゠-ヿ]")
SEOUL = ZoneInfo("Asia/Seoul")


class DCInsideConnector(BaseCommunityConnector):
    connector_name = "dcinside"
    enabled = True
    base_url = "https://gall.dcinside.com"
    mobile_base_url = "https://m.dcinside.com"
    boards = [
        {
            "id": "stockus",
            "board_name": "stockus-concept",
            "list_url": "https://gall.dcinside.com/mgallery/board/lists/?id=stockus&exception_mode=recommend",
            "mobile_list_url": "https://m.dcinside.com/board/stockus?recommend=1",
            "snapshot_file": "stockus_recommend.json",
        },
        {
            "id": "jusik",
            "board_name": "전자주식마이너갤러리",
            "list_url": "https://gall.dcinside.com/mgallery/board/lists/?id=jusik",
            "mobile_list_url": "https://m.dcinside.com/board/jusik",
        },
        {
            "id": "kospi",
            "board_name": "코스피마이너갤러리",
            "list_url": "https://gall.dcinside.com/mgallery/board/lists/?id=kospi",
            "mobile_list_url": "https://m.dcinside.com/board/kospi",
        },
    ]
    board_name_map = {board["id"]: board["board_name"] for board in boards}

    def __init__(self) -> None:
        super().__init__()
        self.analysis_service = CommunityAnalysisService()
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
        self.mobile_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 7.0; SM-G892A Build/NRD90M; wv) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 "
                "Chrome/67.0.3396.87 Mobile Safari/537.36"
            ),
            "Referer": "https://m.dcinside.com/",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        self.snapshot_dir = Path(__file__).resolve().parents[4] / "dcinside_today_2026-03-11"

    def get(self, url: str, **kwargs):
        response = self.session.get(url, timeout=self.settings.request_timeout_seconds, **kwargs)
        response.raise_for_status()
        if not response.encoding or response.encoding.lower() == "iso-8859-1":
            response.encoding = response.apparent_encoding or "utf-8"
        return response

    def get_mobile(self, url: str, **kwargs):
        headers = dict(self.mobile_headers)
        headers.update(kwargs.pop("headers", {}))
        response = requests.get(url, headers=headers, timeout=self.settings.request_timeout_seconds, **kwargs)
        response.raise_for_status()
        if not response.encoding or response.encoding.lower() == "iso-8859-1":
            response.encoding = response.apparent_encoding or "utf-8"
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

        if stubs:
            return stubs

        mobile_stubs = self._fetch_mobile_posts_page(board, page)
        if mobile_stubs:
            return mobile_stubs

        return self._load_snapshot_posts(board, page)

    def fetch_post_detail(self, post_stub: dict[str, Any]) -> dict[str, Any]:
        response = self.get_mobile(post_stub["post_url"]) if "m.dcinside.com" in post_stub["post_url"] else self.get(post_stub["post_url"])
        soup = BeautifulSoup(response.text, "html.parser")

        if "m.dcinside.com" in post_stub["post_url"]:
            return self._parse_mobile_post_detail(post_stub, soup)

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

        if detail["body"] and not self._looks_mojibake(detail["title"]) and not self._looks_mojibake(detail["body"]):
            return detail

        mobile_url = self._build_mobile_post_url(post_stub["board_id"], post_stub["post_no"])
        mobile_response = self.get_mobile(mobile_url)
        mobile_soup = BeautifulSoup(mobile_response.text, "html.parser")
        return self._parse_mobile_post_detail(post_stub, mobile_soup)

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

                    detail = self.fetch_post_detail(stub)
                    normalized = self.normalize_post(self.parse_post(detail))

                    if exists:
                        if self._looks_mojibake(exists.title) or self._looks_mojibake(exists.body):
                            exists.board_name = normalized.board_name
                            exists.title = normalized.title
                            exists.body = normalized.body
                            exists.created_at = datetime.fromisoformat(normalized.created_at)
                            exists.author_hash = anonymize_author(normalized.author_id)
                            exists.view_count = normalized.view_count
                            exists.upvotes = normalized.upvotes
                            exists.downvotes = normalized.downvotes
                            exists.comment_count = normalized.comment_count
                            exists.original_url = normalized.original_url
                            exists.raw_payload = normalized.raw_payload
                            self.analysis_service.persist_post_analysis(db, exists)
                            db.flush()
                        elif not self.analysis_service.read_stored_analysis(exists):
                            self.analysis_service.persist_post_analysis(db, exists)
                        continue

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
                        created_post = db.execute(
                            select(CommunityPost).where(
                                CommunityPost.source_id == source.id,
                                CommunityPost.external_post_id == normalized.external_post_id,
                            )
                        ).scalar_one()
                        self.analysis_service.persist_post_analysis(db, created_post)
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

    def _fetch_mobile_posts_page(self, board: dict[str, str], page: int) -> list[dict]:
        mobile_list_url = board.get("mobile_list_url")
        if not mobile_list_url:
            return []

        response = self.get_mobile(f"{mobile_list_url}&page={page}")
        soup = BeautifulSoup(response.text, "html.parser")
        stubs: list[dict] = []

        for row in soup.select("ul.gall-detail-lst > li"):
            link_node = row.select_one("a.lt")
            title_node = row.select_one("span.subjectin")
            info_nodes = row.select("ul.ginfo > li")
            comment_node = row.select_one("a.rt span.ct")
            author_node = row.select_one("span.blockInfo")
            if not link_node or not title_node:
                continue

            href = link_node.get("href") or ""
            post_no = self._extract_post_no_from_url(href)
            if not post_no:
                continue

            created_at = datetime.now(tz=SEOUL).isoformat()
            if len(info_nodes) >= 3:
                parsed_created_at = self._parse_mobile_list_timestamp(self._safe_text(info_nodes[2]))
                if parsed_created_at is not None:
                    created_at = parsed_created_at.isoformat()

            author_name = author_node.get("data-name") if author_node else None
            author_id = author_node.get("data-info") if author_node else None
            stubs.append(
                {
                    "board_id": board["id"],
                    "board_name": board["board_name"],
                    "external_post_id": f"{board['id']}:{post_no}",
                    "post_no": post_no,
                    "title": self._safe_text(title_node),
                    "post_url": urljoin(self.mobile_base_url, href),
                    "created_at": created_at,
                    "author": self._compose_author(author_name, author_id),
                    "view_count": self._parse_int(self._safe_text(info_nodes[3])) if len(info_nodes) >= 4 else None,
                    "upvotes": self._parse_int(self._safe_text(info_nodes[4])) if len(info_nodes) >= 5 else None,
                    "comment_count": self._parse_int(self._safe_text(comment_node)) if comment_node else None,
                    "raw_row_text": row.get_text(" ", strip=True),
                    "source_mode": "mobile_fallback",
                }
            )

        return stubs

    def _parse_mobile_post_detail(self, post_stub: dict[str, Any], soup: BeautifulSoup) -> dict[str, Any]:
        detail = dict(post_stub)
        title_node = soup.select_one("div.gallview-tit-box span.tit")
        body_node = soup.select_one("div.thum-txtin")
        info_nodes = soup.select("ul.ginfo2 > li")

        detail.update(
            {
                "title": self._extract_mobile_title(title_node) or post_stub["title"],
                "body": clean_text(self._safe_text(body_node)) or clean_text(post_stub["title"]),
                "created_at": self._extract_mobile_detail_created_at(info_nodes) or post_stub["created_at"],
                "view_count": self._extract_mobile_detail_view_count(info_nodes) or post_stub.get("view_count"),
                "upvotes": self._parse_int(self._safe_text(soup.select_one("span#recomm_btn"))) or post_stub.get("upvotes"),
                "author": self._extract_mobile_detail_author(info_nodes) or post_stub.get("author"),
            }
        )
        detail["raw_detail_excerpt"] = detail["body"][:500]
        return detail

    def _load_snapshot_posts(self, board: dict[str, str], page: int) -> list[dict]:
        latest_snapshot = self.snapshot_dir / "combined_latest_100.json"
        aggregate_snapshot = self.snapshot_dir.parent / f"{self.snapshot_dir.name}.json"
        candidates = [
            latest_snapshot,
            aggregate_snapshot,
            self.snapshot_dir / f"{board['id']}.json",
            self.snapshot_dir / board.get("snapshot_file", f"{board['id']}.json"),
        ]
        page_size = 50
        start = (page - 1) * page_size
        end = start + page_size

        best_stubs: list[dict] = []
        best_quality = -1
        for path in candidates:
            if not path.exists():
                continue

            rows = self._read_snapshot_rows(path, board["id"])
            if rows is None:
                continue

            stubs: list[dict] = []
            quality = 0
            for row in rows[start:end]:
                if row.get("gallery_id") != board["id"]:
                    continue
                title = row.get("title", "")
                if title and not self._looks_mojibake(title):
                    quality += 1
                stubs.append(
                    {
                        "board_id": board["id"],
                        "board_name": self.board_name_map.get(board["id"], board["board_name"]),
                        "external_post_id": f"{board['id']}:{row['post_no']}",
                        "post_no": str(row["post_no"]),
                        "title": title,
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

            if quality > best_quality:
                best_quality = quality
                best_stubs = stubs

        return best_stubs

    @staticmethod
    def _read_snapshot_rows(path: Path, board_id: str) -> list[dict] | None:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

        if isinstance(payload, dict):
            rows = payload.get(board_id)
            if isinstance(rows, list):
                return rows
            return None

        if isinstance(payload, list):
            return payload

        return None

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

    @staticmethod
    def _looks_mojibake(value: str | None) -> bool:
        if not value:
            return False
        hangul_count = len(HANGUL_RE.findall(value))
        weird_characters = len(MOJIBAKE_RE.findall(value))
        if weird_characters < 2:
            return False
        return hangul_count == 0 or weird_characters > hangul_count * 2

    @staticmethod
    def _build_mobile_post_url(board_id: str, post_no: str) -> str:
        return f"https://m.dcinside.com/board/{board_id}/{post_no}"

    @staticmethod
    def _extract_post_no_from_url(url: str) -> str | None:
        parsed = urlparse(url)
        path_parts = [part for part in parsed.path.split("/") if part]
        if path_parts and path_parts[-1].isdigit():
            return path_parts[-1]

        query_post_no = parse_qs(parsed.query).get("no", [])
        if query_post_no and query_post_no[0].isdigit():
            return query_post_no[0]
        return None

    @staticmethod
    def _parse_mobile_list_timestamp(value: str) -> datetime | None:
        text = (value or "").strip()
        if not text:
            return None

        now_kst = datetime.now(tz=SEOUL)
        for fmt in ("%H:%M", "%m.%d", "%Y.%m.%d %H:%M", "%Y.%m.%d %H:%M:%S"):
            try:
                parsed = datetime.strptime(text, fmt)
                if fmt == "%H:%M":
                    return now_kst.replace(hour=parsed.hour, minute=parsed.minute, second=0, microsecond=0)
                if fmt == "%m.%d":
                    return now_kst.replace(
                        month=parsed.month,
                        day=parsed.day,
                        hour=23,
                        minute=59,
                        second=59,
                        microsecond=0,
                    )
                return parsed.replace(tzinfo=SEOUL)
            except ValueError:
                continue
        return None

    @staticmethod
    def _compose_author(author_name: str | None, author_id: str | None) -> str | None:
        if author_name and author_id:
            return f"{author_name} ({author_id})"
        return author_name or author_id

    @staticmethod
    def _extract_mobile_title(node: Any) -> str:
        text = DCInsideConnector._safe_text(node)
        return re.sub(r"^\[[^\]]+\]\s*", "", text).strip()

    @staticmethod
    def _extract_mobile_detail_author(info_nodes: list[Any]) -> str | None:
        if not info_nodes:
            return None
        text = DCInsideConnector._safe_text(info_nodes[0])
        return text or None

    @staticmethod
    def _extract_mobile_detail_created_at(info_nodes: list[Any]) -> str | None:
        if len(info_nodes) < 2:
            return None
        text = DCInsideConnector._safe_text(info_nodes[1])
        for fmt in ("%Y.%m.%d %H:%M", "%Y.%m.%d %H:%M:%S"):
            try:
                return datetime.strptime(text, fmt).replace(tzinfo=SEOUL).isoformat()
            except ValueError:
                continue
        return None

    @staticmethod
    def _extract_mobile_detail_view_count(info_nodes: list[Any]) -> int | None:
        if len(info_nodes) < 3:
            return None
        return DCInsideConnector._parse_int(DCInsideConnector._safe_text(info_nodes[2]))
