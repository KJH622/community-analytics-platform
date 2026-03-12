from __future__ import annotations

import re
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from playwright.sync_api import BrowserContext, Page, Route, TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
from sqlalchemy.orm import Session

from app.collectors.base.contracts import CollectorResult
from app.collectors.communities.live_forums import BaseLiveCommunityConnector, BoardConfig
from app.utils.text import clean_text

SEOUL = ZoneInfo("Asia/Seoul")
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/137.0.0.0 Safari/537.36"
)


class ArcaLiveConnector(BaseLiveCommunityConnector):
    connector_name = "arca_live"
    source_name = "Arca Live"
    base_url = "https://arca.live"
    boards = [BoardConfig(code="stock", name="주식 채널", topic_hint="economy", supports_history=False)]
    compliance_note = (
        "Uses standard Playwright browser rendering for the public stock board without login, stealth, or "
        "challenge-bypass tooling."
    )
    max_posts_per_run = 20

    def __init__(self) -> None:
        super().__init__()
        self._browser_context: BrowserContext | None = None

    def collect(self, db: Session) -> CollectorResult:
        return self.collect_recent(db)

    def collect_recent(self, db: Session) -> CollectorResult:
        self._collection_mode = "recent"
        board = self.boards[0]
        source = self._ensure_source(db)

        with self._browser_session():
            stubs = self.fetch_posts_page(board=board, page=1)
            processed = 0

            for stub in stubs[: self.max_posts_per_run]:
                detail = self.fetch_post_detail(stub)
                parsed = self.parse_post({**stub, **detail})
                normalized = self.normalize_post(parsed)
                self._upsert_post(db, source, normalized)
                processed += 1
                time.sleep(max(self.settings.community_request_interval_seconds, 0.2))

            source.metadata_json = {
                **(source.metadata_json or {}),
                "last_collected_at": datetime.now(tz=timezone.utc).isoformat(),
                "last_board_counts": {
                    **(source.metadata_json.get("last_board_counts", {}) if source.metadata_json else {}),
                    board.code: processed,
                },
            }
            db.commit()

        return CollectorResult(
            name=self.connector_name,
            records_processed=processed,
            message=f"Stored or refreshed {processed} posts from {self.source_name}.",
        )

    def collect_history(self, db: Session, days: int | None = None) -> CollectorResult:
        return CollectorResult(
            name=self.connector_name,
            message="Arca Live history backfill is not enabled in this app.",
            records_processed=0,
        )

    def fetch_posts_page(self, board: BoardConfig, page: int = 1) -> list[dict]:
        list_page = self._open_page(
            f"{self.base_url}/b/{board.code}?p={page}",
            wait_selector="a.vrow.column[href^='/b/stock/']",
            wait_ms=6000,
        )

        try:
            rows = list_page.locator("a.vrow.column[href^='/b/stock/']")
            posts: list[dict] = []

            for index in range(rows.count()):
                row = rows.nth(index)
                row_classes = row.get_attribute("class") or ""
                if "notice" in row_classes or "notice-unfilter" in row_classes:
                    continue

                href = row.get_attribute("href") or ""
                post_id_match = re.search(r"/b/stock/(\d+)", href)
                if not post_id_match:
                    continue

                created_attr = self._locator_attr(row, ".col-time time", "datetime")
                created_at = self._parse_datetime(created_attr)
                if created_at is None:
                    continue

                title = clean_text(self._locator_text(row, ".col-title .title"))
                if not title:
                    continue

                author = clean_text(self._locator_text(row, ".col-author [data-filter]")) or None
                post_url = f"{self.base_url}{href}"
                posts.append(
                    {
                        "board_code": board.code,
                        "board_name": board.name,
                        "topic_category": board.topic_hint,
                        "external_post_id": f"{board.code}:{post_id_match.group(1)}",
                        "title": title,
                        "post_url": post_url,
                        "author": author,
                        "created_at": created_at,
                        "view_count": self._to_int(self._locator_text(row, ".col-view")),
                        "upvotes": self._to_int(self._locator_text(row, ".col-rate")),
                        "downvotes": None,
                        "comment_count": self._to_int(self._locator_text(row, ".comment-count")),
                    }
                )

                if len(posts) >= self.max_posts_per_run:
                    break

            posts.sort(key=lambda item: item["created_at"], reverse=True)
            return posts
        finally:
            list_page.close()

    def fetch_post_detail(self, post_stub: dict) -> dict:
        detail_page = self._open_page(
            post_stub["post_url"],
            wait_selector=".fr-view.article-content",
            wait_ms=1500,
        )

        try:
            body = clean_text(self._page_text(detail_page, ".fr-view.article-content", separator="\n"))
            return {
                "body": body or post_stub["title"],
            }
        finally:
            detail_page.close()

    def parse_post(self, payload: dict) -> dict:
        return payload

    @contextmanager
    def _browser_session(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(
                locale="ko-KR",
                timezone_id="Asia/Seoul",
                user_agent=USER_AGENT,
                viewport={"width": 1440, "height": 2200},
            )
            context.route("**/*", self._route_request)
            self._browser_context = context
            try:
                yield
            finally:
                self._browser_context = None
                context.close()
                browser.close()

    @staticmethod
    def _route_request(route: Route) -> None:
        if route.request.resource_type in {"image", "media", "font"}:
            route.abort()
            return
        route.continue_()

    def _open_page(self, url: str, wait_selector: str, wait_ms: int) -> Page:
        if self._browser_context is None:
            raise RuntimeError("Arca browser context is not initialized.")

        page = self._browser_context.new_page()
        response = page.goto(url, wait_until="domcontentloaded", timeout=45000)
        if response is None:
            page.close()
            raise RuntimeError(f"Arca Live did not return a response for {url}")

        page.wait_for_timeout(wait_ms)
        try:
            page.wait_for_selector(wait_selector, timeout=12000)
        except PlaywrightTimeoutError as exc:
            html = page.content()
            page.close()
            if "Just a moment..." in html or "cf_chl_opt" in html:
                raise RuntimeError("Arca Live returned a challenge page.") from exc
            raise RuntimeError(f"Arca Live selector did not appear for {url}") from exc

        html = page.content()
        if "Just a moment..." in html or "cf_chl_opt" in html:
            page.close()
            raise RuntimeError("Arca Live returned a challenge page.")
        return page

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None

        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=SEOUL)
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _locator_text(root: Page | object, selector: str, separator: str = " ") -> str:
        locator = root.locator(selector)  # type: ignore[attr-defined]
        if locator.count() == 0:
            return ""
        try:
            return locator.first.inner_text(timeout=3000).replace("\n", separator).strip()
        except PlaywrightTimeoutError:
            return ""

    @staticmethod
    def _locator_attr(root: Page | object, selector: str, attribute: str) -> str | None:
        locator = root.locator(selector)  # type: ignore[attr-defined]
        if locator.count() == 0:
            return None
        try:
            return locator.first.get_attribute(attribute, timeout=3000)
        except PlaywrightTimeoutError:
            return None

    def _page_text(self, page: Page, selector: str, separator: str = " ") -> str:
        return self._locator_text(page, selector, separator=separator)
