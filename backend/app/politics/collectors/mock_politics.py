from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.politics.collectors.base import BasePoliticalCommunityConnector, PoliticalNormalizedPost
from app.politics.models import PoliticalCommunitySource, PoliticalPost
from app.utils.text import clean_text


class MockPoliticsConnector(BasePoliticalCommunityConnector):
    connector_name = "mock_politics_forum"
    enabled = True

    def fetch_posts_page(self) -> list[dict]:
        return [
            {
                "id": "politics-demo-001",
                "title": "대선 후보 토론 이후 지지층 결집 분위기",
                "body": "후보 토론 이후 지지와 반대가 강하게 갈리며 정치 양극화가 커지는 모습이다.",
                "view_count": 2210,
                "upvotes": 88,
                "comment_count": 53,
                "url": "https://example.local/politics/001",
            },
            {
                "id": "politics-demo-002",
                "title": "정당 지지율보다 정책 평가가 더 중요하다는 의견",
                "body": "정당보다 정책과 국정수행 평가를 봐야 한다는 글이 늘고 있다.",
                "view_count": 1740,
                "upvotes": 65,
                "comment_count": 34,
                "url": "https://example.local/politics/002",
            },
        ]

    def fetch_post_detail(self, post_stub: dict) -> dict:
        return post_stub

    def parse_post(self, payload: dict) -> dict:
        return payload

    def normalize_post(self, parsed: dict) -> PoliticalNormalizedPost:
        return PoliticalNormalizedPost(
            source_code=self.connector_name,
            community_name="Mock Political Forum",
            board_name="election-room",
            external_post_id=parsed["id"],
            title=clean_text(parsed["title"]),
            body=clean_text(parsed["body"]),
            created_at=datetime.now(tz=timezone.utc).isoformat(),
            view_count=parsed.get("view_count"),
            upvotes=parsed.get("upvotes"),
            comment_count=parsed.get("comment_count"),
            original_url=parsed["url"],
            raw_payload=parsed,
        )

    def collect(self, db: Session) -> int:
        source = db.execute(
            select(PoliticalCommunitySource).where(PoliticalCommunitySource.code == self.connector_name)
        ).scalar_one_or_none()
        if source is None:
            source = PoliticalCommunitySource(
                code=self.connector_name,
                name="Mock Political Forum",
                description="Safe connector for politics analytics local development.",
                leaning="unknown",
                link="https://example.local/politics",
                board_name="election-room",
                status="mock",
                compliance_notes="Mock only. No live crawling.",
                metadata_json={},
            )
            db.add(source)
            db.flush()

        inserted = 0
        for stub in self.fetch_posts_page():
            normalized = self.normalize_post(self.parse_post(self.fetch_post_detail(stub)))
            exists = db.execute(
                select(PoliticalPost).where(
                    PoliticalPost.source_code == normalized.source_code,
                    PoliticalPost.external_post_id == normalized.external_post_id,
                )
            ).scalar_one_or_none()
            if exists:
                continue
            db.add(
                PoliticalPost(
                    source_code=normalized.source_code,
                    community_name=normalized.community_name,
                    board_name=normalized.board_name,
                    external_post_id=normalized.external_post_id,
                    title=normalized.title,
                    body=normalized.body,
                    created_at=datetime.fromisoformat(normalized.created_at),
                    view_count=normalized.view_count,
                    upvotes=normalized.upvotes,
                    comment_count=normalized.comment_count,
                    original_url=normalized.original_url,
                    raw_payload=normalized.raw_payload,
                )
            )
            inserted += 1
        db.commit()
        return inserted
