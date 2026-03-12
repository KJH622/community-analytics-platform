from __future__ import annotations

import random
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse
from zoneinfo import ZoneInfo

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_fixed

from app.collectors.base.contracts import CollectorResult
from app.collectors.communities.base import BaseCommunityConnector, NormalizedCommunityPost
from app.models import CommunityPost, Source, SourceType
from app.services.text_processor import anonymize_author
from app.utils.text import clean_text

SEOUL = ZoneInfo("Asia/Seoul")
BOBAE_DETAIL_RE = re.compile(
    r"조회\s*(?P<views>\d+)\s*\|\s*추천\s*(?P<upvotes>\d+)\s*\|\s*반대\s*(?P<downvotes>\d+)\s*\|\s*(?P<created>\d{4}\.\d{2}\.\d{2}).*?(?P<time>\d{2}:\d{2})"
)


@dataclass(frozen=True)
class BoardConfig:
    code: str
    name: str
    topic_hint: str | None = None
    supports_history: bool = True


class CommunityTopicClassifier:
    politics_keywords = {
        "정치",
        "시사",
        "대통령",
        "대통령실",
        "국회",
        "의원",
        "장관",
        "정당",
        "민주당",
        "국민의힘",
        "조국",
        "개혁신당",
        "선거",
        "총선",
        "대선",
        "탄핵",
        "검찰",
        "법원",
        "헌재",
        "여당",
        "야당",
        "공수처",
        "윤석열",
        "이재명",
        "한동훈",
        "조국혁신당",
        "국정",
        "정책",
        "외교",
    }
    economy_keywords = {
        "경제",
        "증시",
        "주식",
        "국장",
        "미장",
        "코스피",
        "코스닥",
        "비트코인",
        "코인",
        "가상화폐",
        "환율",
        "금리",
        "연준",
        "fed",
        "cpi",
        "ppi",
        "유가",
        "물가",
        "부동산",
        "집값",
        "청약",
        "매매",
        "재테크",
        "예금",
        "적금",
        "대출",
        "세금",
        "월세",
        "전세",
        "임대",
        "실업",
        "경기",
    }

    def title_is_relevant(self, title: str) -> bool:
        return self._score(title)[0] > 0 or self._score(title)[1] > 0

    def classify(self, title: str, body: str) -> str | None:
        politics_score, economy_score = self._score(title, weight=2)
        body_politics, body_economy = self._score(body, weight=1)
        politics_score += body_politics
        economy_score += body_economy

        if politics_score == 0 and economy_score == 0:
            return None
        if politics_score > economy_score:
            return "politics"
        if economy_score > politics_score:
            return "economy"
        return None

    def _score(self, text: str, weight: int = 1) -> tuple[int, int]:
        lowered = clean_text(text or "").lower()
        politics = sum(weight for keyword in self.politics_keywords if keyword in lowered)
        economy = sum(weight for keyword in self.economy_keywords if keyword in lowered)
        return politics, economy


class BaseLiveCommunityConnector(BaseCommunityConnector):
    connector_name = "live_forum"
    source_name = "Live Forum"
    base_url = ""
    boards: list[BoardConfig] = []

    def __init__(self) -> None:
        super().__init__()
        self.classifier = CommunityTopicClassifier()
        self._last_request_finished_at = 0.0
        self._collection_mode = "recent"
        self.client.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            }
        )

    def fetch_board_metadata(self) -> dict:
        return {
            "source": self.connector_name,
            "boards": [
                {
                    "code": board.code,
                    "name": board.name,
                    "topic_hint": board.topic_hint,
                    "supports_history": board.supports_history,
                }
                for board in self.boards
            ],
        }

    def collect(self, db: Session) -> CollectorResult:
        return self.collect_recent(db)

    def collect_recent(self, db: Session) -> CollectorResult:
        self._collection_mode = "recent"
        since = datetime.now(tz=timezone.utc) - timedelta(hours=2)
        return self._collect(db, since=since, max_pages=self.settings.community_incremental_pages_per_board)

    def collect_history(self, db: Session, days: int | None = None) -> CollectorResult:
        self._collection_mode = "history"
        history_days = days or self.settings.community_history_days
        since = datetime.now(tz=timezone.utc) - timedelta(days=history_days)
        return self._collect(db, since=since, max_pages=self.settings.community_history_max_pages_per_board)

    def _collect(self, db: Session, since: datetime, max_pages: int) -> CollectorResult:
        source = self._ensure_source(db)
        processed = 0

        for board in self.boards:
            board_total = 0
            board_pages = 1 if not board.supports_history else max_pages
            existing_ids = self._existing_external_ids(db, source.id, board.code)
            for page in range(1, board_pages + 1):
                stubs = self.fetch_posts_page(board=board, page=page)
                if not stubs:
                    break

                reached_cutoff = False
                for stub in stubs:
                    if stub["created_at"] < since:
                        reached_cutoff = True
                        continue

                    if self._collection_mode == "history" and stub["external_post_id"] in existing_ids:
                        continue

                    if board.topic_hint is None and not self.classifier.title_is_relevant(stub["title"]):
                        continue

                    detail = self.fetch_post_detail(stub)
                    parsed = self.parse_post({**stub, **detail})
                    normalized = self.normalize_post(parsed)
                    if normalized.topic_category is None:
                        continue

                    self._upsert_post(db, source, normalized)
                    existing_ids.add(normalized.external_post_id)
                    processed += 1
                    board_total += 1

                    if processed % 100 == 0:
                        db.commit()

                if reached_cutoff:
                    break

            source.metadata_json = {
                **(source.metadata_json or {}),
                "last_collected_at": datetime.now(tz=timezone.utc).isoformat(),
                "last_board_counts": {
                    **(source.metadata_json.get("last_board_counts", {}) if source.metadata_json else {}),
                    board.code: board_total,
                },
            }
            db.flush()

        db.commit()
        return CollectorResult(
            name=self.connector_name,
            records_processed=processed,
            message=f"Stored or refreshed {processed} posts from {self.source_name}.",
        )

    def parse_post(self, payload: dict[str, Any]) -> dict[str, Any]:
        return payload

    def normalize_post(self, parsed: dict[str, Any]) -> NormalizedCommunityPost:
        title = clean_text(parsed["title"])
        body = clean_text(parsed.get("body") or title)
        topic_category = parsed.get("topic_category") or self.classifier.classify(title, body)

        created_at = parsed["created_at"]
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=SEOUL)
        created_at = created_at.astimezone(timezone.utc)

        payload = {
            **parsed,
            "source_code": self.connector_name,
            "source_name": self.source_name,
            "board_code": parsed["board_code"],
            "board_name": parsed["board_name"],
            "topic_category": topic_category,
            "created_at": created_at.isoformat(),
        }

        return NormalizedCommunityPost(
            board_code=parsed["board_code"],
            board_name=parsed["board_name"],
            topic_category=topic_category,
            external_post_id=parsed["external_post_id"],
            title=title,
            body=body,
            created_at=created_at.isoformat(),
            author_id=parsed.get("author"),
            view_count=parsed.get("view_count"),
            upvotes=parsed.get("upvotes"),
            downvotes=parsed.get("downvotes"),
            comment_count=parsed.get("comment_count"),
            original_url=parsed["post_url"],
            raw_payload=payload,
        )

    def _ensure_source(self, db: Session) -> Source:
        source = db.execute(select(Source).where(Source.code == self.connector_name)).scalar_one_or_none()
        if source is not None:
            return source

        source = Source(
            code=self.connector_name,
            name=self.source_name,
            source_type=SourceType.COMMUNITY,
            country="KR",
            base_url=self.base_url,
            is_official=False,
            compliance_notes=self.compliance_note,
            metadata_json=self.fetch_board_metadata(),
        )
        db.add(source)
        db.flush()
        return source

    def _upsert_post(self, db: Session, source: Source, normalized: NormalizedCommunityPost) -> None:
        existing = db.execute(
            select(CommunityPost).where(
                CommunityPost.source_id == source.id,
                CommunityPost.external_post_id == normalized.external_post_id,
            )
        ).scalar_one_or_none()
        if existing is None:
            db.add(
                CommunityPost(
                    source_id=source.id,
                    board_code=normalized.board_code,
                    board_name=normalized.board_name,
                    topic_category=normalized.topic_category,
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
            return

        existing.board_code = normalized.board_code
        existing.board_name = normalized.board_name
        existing.topic_category = normalized.topic_category
        existing.title = normalized.title
        existing.body = normalized.body
        existing.created_at = datetime.fromisoformat(normalized.created_at)
        existing.author_hash = anonymize_author(normalized.author_id)
        existing.view_count = normalized.view_count
        existing.upvotes = normalized.upvotes
        existing.downvotes = normalized.downvotes
        existing.comment_count = normalized.comment_count
        existing.original_url = normalized.original_url
        existing.raw_payload = normalized.raw_payload

    @staticmethod
    def _existing_external_ids(db: Session, source_id: int, board_code: str) -> set[str]:
        rows = db.execute(
            select(CommunityPost.external_post_id).where(
                CommunityPost.source_id == source_id,
                CommunityPost.board_code == board_code,
            )
        ).scalars().all()
        return set(rows)

    @staticmethod
    def _parse_query_value(url: str, key: str) -> str:
        parsed = urlparse(url)
        values = parse_qs(parsed.query).get(key)
        if values:
            return values[0]
        return ""

    @staticmethod
    def _to_int(value: str | None) -> int | None:
        if not value:
            return None
        digits = re.sub(r"[^\d]", "", value)
        return int(digits) if digits else None

    @staticmethod
    def _current_seoul() -> datetime:
        return datetime.now(tz=SEOUL)

    @staticmethod
    def _node_text(node: Any, separator: str = " ") -> str:
        if node is None:
            return ""
        return clean_text(node.get_text(separator, strip=True))

    @staticmethod
    def _node_attr(node: Any, key: str) -> str:
        if node is None:
            return ""
        return clean_text(node.get(key) or "")

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
    def get(self, url: str, **kwargs) -> httpx.Response:
        self._throttle()
        try:
            response = self.client.get(url, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in {403, 429}:
                time.sleep(10)
            raise
        finally:
            self._last_request_finished_at = time.monotonic()

    def _throttle(self) -> None:
        min_interval = self._min_interval_seconds()
        jitter = random.uniform(0, max(self.settings.community_request_jitter_seconds, 0.0))
        target_interval = min_interval + jitter
        elapsed = time.monotonic() - self._last_request_finished_at
        wait_seconds = target_interval - elapsed
        if wait_seconds > 0:
            time.sleep(wait_seconds)

    def _min_interval_seconds(self) -> float:
        if self._collection_mode == "history":
            return max(self.settings.community_backfill_request_interval_seconds, 0.1)
        return max(self.settings.community_request_interval_seconds, 0.1)


class PpomppuConnector(BaseLiveCommunityConnector):
    connector_name = "ppomppu"
    source_name = "PPOMPPU"
    base_url = "https://www.ppomppu.co.kr"
    boards = [
        BoardConfig(code="issue", name="정치자유게시판", topic_hint="politics"),
        BoardConfig(code="money", name="재테크포럼", topic_hint="economy"),
        BoardConfig(code="stock", name="증권포럼", topic_hint="economy"),
        BoardConfig(code="house", name="부동산포럼", topic_hint="economy"),
    ]
    compliance_note = "robots.txt allows /zboard/ paths; this connector uses public board and post pages only."

    def __init__(self) -> None:
        super().__init__()
        self.client.headers.update({"Referer": f"{self.base_url}/"})

    def fetch_posts_page(self, board: BoardConfig, page: int = 1) -> list[dict]:
        response = self.get(f"{self.base_url}/zboard/zboard.php?id={board.code}&page={page}")
        response.encoding = "euc-kr"
        soup = BeautifulSoup(response.text, "html.parser")
        posts: list[dict] = []

        for row in soup.select("tr.baseList"):
            link = row.select_one(f'a.baseList-title[href*="id={board.code}"]')
            if link is None:
                continue

            href = link.get("href", "")
            if not href or f"id={board.code}" not in href:
                continue

            title = clean_text(link.get_text(" ", strip=True))
            post_url = urljoin(f"{self.base_url}/zboard/", href)
            post_no = self._parse_query_value(post_url, "no")
            if not post_no:
                continue

            author = self._node_text(row.select_one("span.baseList-name"))
            time_cell = row.select_one('td[title]')
            time_text = self._node_attr(time_cell, "title") or self._node_text(
                row.select_one("time.baseList-time")
            )
            created_at = self._parse_ppomppu_datetime(time_text)
            if created_at is None:
                continue

            recommend_text = self._node_text(row.select_one("td.baseList-rec"))
            upvotes, downvotes = self._parse_recommend_pair(recommend_text)

            posts.append(
                {
                    "board_code": board.code,
                    "board_name": board.name,
                    "topic_category": board.topic_hint,
                    "external_post_id": f"{board.code}:{post_no}",
                    "title": title,
                    "post_url": post_url,
                    "author": author or None,
                    "created_at": created_at,
                    "view_count": self._to_int(self._node_text(row.select_one("td.baseList-views"))),
                    "upvotes": upvotes,
                    "downvotes": downvotes,
                    "comment_count": self._to_int(self._node_text(row.select_one("span.baseList-c"))),
                }
            )

        return posts

    def fetch_post_detail(self, post_stub: dict) -> dict:
        response = self.get(post_stub["post_url"])
        response.encoding = "euc-kr"
        soup = BeautifulSoup(response.text, "html.parser")
        body = self._node_text(soup.select_one("td.board-contents"), separator="\n")
        return {"body": body or post_stub["title"]}

    @staticmethod
    def _parse_recommend_pair(value: str) -> tuple[int | None, int | None]:
        match = re.search(r"(\d+)\s*-\s*(\d+)", value)
        if not match:
            return None, None
        return int(match.group(1)), int(match.group(2))

    @staticmethod
    def _parse_ppomppu_datetime(value: str) -> datetime | None:
        text = clean_text(value)
        for fmt in ("%y.%m.%d %H:%M:%S", "%y/%m/%d", "%y.%m.%d", "%H:%M:%S"):
            try:
                parsed = datetime.strptime(text, fmt)
                if fmt == "%H:%M:%S":
                    now = BaseLiveCommunityConnector._current_seoul()
                    parsed = parsed.replace(year=now.year, month=now.month, day=now.day)
                return parsed.replace(tzinfo=SEOUL)
            except ValueError:
                continue
        return None


class BobaedreamConnector(BaseLiveCommunityConnector):
    connector_name = "bobaedream"
    source_name = "Bobaedream"
    base_url = "https://www.bobaedream.co.kr"
    boards = [
        BoardConfig(code="politic", name="정치/시사게시판", topic_hint="politics"),
        BoardConfig(code="freeb", name="자유게시판", supports_history=False),
    ]
    compliance_note = "robots.txt currently allows public board and post pages."

    def fetch_posts_page(self, board: BoardConfig, page: int = 1) -> list[dict]:
        response = self.get(f"{self.base_url}/list?code={board.code}&page={page}")
        soup = BeautifulSoup(response.text, "html.parser")
        posts: list[dict] = []

        for row in soup.select('tr[itemtype="http://schema.org/Article"]'):
            link = row.select_one(f'td.pl14 a.bsubject[href*="code={board.code}"]')
            if link is None:
                continue

            post_url = urljoin(self.base_url, link.get("href", ""))
            post_no = self._parse_query_value(post_url, "No")
            if not post_no:
                continue

            created_at = self._parse_bobae_list_datetime(
                self._node_text(row.select_one("td.date"))
            )
            if created_at is None:
                continue

            title = clean_text(link.get("title") or link.get_text(" ", strip=True))
            posts.append(
                {
                    "board_code": board.code,
                    "board_name": board.name,
                    "topic_category": board.topic_hint,
                    "external_post_id": f"{board.code}:{post_no}",
                    "title": title,
                    "post_url": post_url,
                    "author": self._node_text(row.select_one("span.author")) or None,
                    "created_at": created_at,
                    "view_count": self._to_int(self._node_text(row.select_one("td.count"))),
                    "upvotes": self._to_int(self._node_text(row.select_one("td.recomm"))),
                    "downvotes": None,
                    "comment_count": None,
                }
            )

        return posts

    def fetch_post_detail(self, post_stub: dict) -> dict:
        response = self.get(post_stub["post_url"])
        soup = BeautifulSoup(response.text, "html.parser")
        body = self._node_text(soup.select_one("div.bodyCont"), separator="\n")
        author = self._node_text(soup.select_one("a.nickName")) or post_stub.get("author")

        count_group = self._node_text(soup.select_one("span.countGroup"))
        detail_match = BOBAE_DETAIL_RE.search(count_group)
        created_at = post_stub["created_at"]
        view_count = post_stub.get("view_count")
        upvotes = post_stub.get("upvotes")
        downvotes = post_stub.get("downvotes")
        if detail_match:
            created_at = datetime.strptime(
                f"{detail_match.group('created')} {detail_match.group('time')}", "%Y.%m.%d %H:%M"
            ).replace(tzinfo=SEOUL)
            view_count = int(detail_match.group("views"))
            upvotes = int(detail_match.group("upvotes"))
            downvotes = int(detail_match.group("downvotes"))

        title = self._node_text(soup.select_one('strong[itemprop="name"]'))
        return {
            "title": title or post_stub["title"],
            "body": body or post_stub["title"],
            "author": author,
            "created_at": created_at,
            "view_count": view_count,
            "upvotes": upvotes,
            "downvotes": downvotes,
        }

    @staticmethod
    def _parse_bobae_list_datetime(value: str) -> datetime | None:
        text = clean_text(value)
        now = BaseLiveCommunityConnector._current_seoul()
        try:
            parsed = datetime.strptime(text, "%H:%M")
            return parsed.replace(year=now.year, month=now.month, day=now.day, tzinfo=SEOUL)
        except ValueError:
            pass

        try:
            parsed = datetime.strptime(text, "%m/%d")
            year = now.year
            if (parsed.month, parsed.day) > (now.month, now.day):
                year -= 1
            return parsed.replace(year=year, tzinfo=SEOUL)
        except ValueError:
            return None


class ClienConnector(BaseLiveCommunityConnector):
    connector_name = "clien"
    source_name = "Clien"
    base_url = "https://www.clien.net"
    boards = [
        BoardConfig(code="park", name="모두의공원", supports_history=False),
        BoardConfig(code="cm_stock", name="주식한당", topic_hint="economy", supports_history=False),
        BoardConfig(code="cm_vcoin", name="가상화폐당", topic_hint="economy", supports_history=False),
    ]
    compliance_note = (
        "robots.txt allows /service/board/ paths but disallows query strings, so this connector only uses the first "
        "page and queryless post URLs."
    )

    def fetch_posts_page(self, board: BoardConfig, page: int = 1) -> list[dict]:
        if page > 1:
            return []

        response = self.get(f"{self.base_url}/service/board/{board.code}")
        soup = BeautifulSoup(response.text, "html.parser")
        posts: list[dict] = []

        for item in soup.select("div.list_item"):
            item_classes = item.get("class", [])
            if "notice" in item_classes or "hongbo" in item_classes:
                continue

            link = item.select_one("a.list_subject")
            title_node = item.select_one("span.subject_fixed")
            if link is None or title_node is None:
                continue

            post_url = urljoin(self.base_url, (link.get("href", "")).split("?")[0])
            post_no = item.get("data-board-sn") or post_url.rstrip("/").split("/")[-1]
            title = clean_text(title_node.get("title") or link.get_text(" ", strip=True))
            created_text = self._node_text(item.select_one(".list_time .timestamp"))
            created_at = self._parse_clien_datetime(created_text)
            if created_at is None:
                continue

            author_node = item.select_one(".nickname span[title]")
            author = self._node_text(author_node or item.select_one(".nickname")) or None
            posts.append(
                {
                    "board_code": board.code,
                    "board_name": board.name,
                    "topic_category": board.topic_hint,
                    "external_post_id": f"{board.code}:{post_no}",
                    "title": title,
                    "post_url": post_url,
                    "author": author,
                    "created_at": created_at,
                    "view_count": self._to_int(self._node_text(item.select_one(".list_hit .hit"))),
                    "upvotes": self._to_int(self._node_text(item.select_one(".list_symph span"))),
                    "downvotes": None,
                    "comment_count": self._to_int(item.get("data-comment-count")),
                }
            )

        return posts

    def fetch_post_detail(self, post_stub: dict) -> dict:
        response = self.get(post_stub["post_url"])
        soup = BeautifulSoup(response.text, "html.parser")
        article = soup.select_one("div.post_article") or soup.select_one("div.post_content")
        body = self._node_text(article, separator="\n")
        author_meta = soup.select_one("div.post_author")
        created_at = post_stub["created_at"]
        view_count = post_stub.get("view_count")
        if author_meta is not None:
            date_text = self._node_text(author_meta.select_one(".view_count.date"))
            maybe_created = self._parse_clien_datetime(date_text)
            if maybe_created is not None:
                created_at = maybe_created
            view_count = self._to_int(self._node_text(author_meta.select_one("strong"))) or view_count

        title = self._node_text(soup.select_one("div.post_title h3 span"))
        return {
            "title": title or post_stub["title"],
            "body": body or post_stub["title"],
            "created_at": created_at,
            "view_count": view_count,
        }

    @staticmethod
    def _parse_clien_datetime(value: str) -> datetime | None:
        text = clean_text(value)
        try:
            return datetime.strptime(text, "%Y-%m-%d %H:%M:%S").replace(tzinfo=SEOUL)
        except ValueError:
            return None
