from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.collectors.base.contracts import CollectorResult
from app.collectors.communities.base import BaseCommunityConnector, NormalizedCommunityPost
from app.models import CommunityPost, Source, SourceType
from app.services.text_processor import anonymize_author
from app.utils.text import clean_text


class MockForumConnector(BaseCommunityConnector):
    connector_name = "mock_forum"
    enabled = True

    def fetch_board_metadata(self) -> dict:
        return {"board_name": "demo-market-board", "live": False}

    def fetch_posts_page(self) -> list[dict]:
        return [
            {
                "id": "demo-001",
                "title": "엔비디아 또 간다 vs 너무 과열 같다",
                "body": "반도체 랠리는 좋은데 너무 과열 같아서 관망 의견도 많다.",
                "author": "user-1",
                "view_count": 1234,
                "upvotes": 45,
                "downvotes": 7,
                "comment_count": 11,
                "url": "https://example.local/community/demo-001",
            }
        ]

    def fetch_post_detail(self, post_stub: dict) -> dict:
        return post_stub

    def parse_post(self, payload: dict) -> dict:
        return payload

    def normalize_post(self, parsed: dict) -> NormalizedCommunityPost:
        return NormalizedCommunityPost(
            board_name="demo-market-board",
            external_post_id=parsed["id"],
            title=clean_text(parsed["title"]),
            body=clean_text(parsed["body"]),
            created_at=datetime.now(tz=timezone.utc).isoformat(),
            author_id=parsed.get("author"),
            view_count=parsed.get("view_count"),
            upvotes=parsed.get("upvotes"),
            downvotes=parsed.get("downvotes"),
            comment_count=parsed.get("comment_count"),
            original_url=parsed["url"],
            raw_payload=parsed,
        )

    def collect(self, db: Session) -> CollectorResult:
        source = db.execute(select(Source).where(Source.code == self.connector_name)).scalar_one_or_none()
        if source is None:
            source = Source(
                code=self.connector_name,
                name="Mock Community Forum",
                source_type=SourceType.COMMUNITY,
                country="KR",
                base_url="https://example.local/community",
                is_official=False,
                compliance_notes="Mock connector for safe local development only.",
            )
            db.add(source)
            db.flush()

        processed = 0
        for stub in self.fetch_posts_page():
            detail = self.fetch_post_detail(stub)
            normalized = self.normalize_post(self.parse_post(detail))
            exists = db.execute(
                select(CommunityPost).where(
                    CommunityPost.source_id == source.id,
                    CommunityPost.external_post_id == normalized.external_post_id,
                )
            ).scalar_one_or_none()
            if exists:
                continue
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
            processed += 1
        db.commit()
        return CollectorResult(name=self.connector_name, records_processed=processed, message="Stored mock community posts.")
