from datetime import datetime, timezone

from app.collectors.base.contracts import CollectorResult
from app.collectors.communities.dcinside import DCInsideConnector
from app.models import CommunityPost, Source, SourceType


def test_list_community_posts_includes_analysis(api_client, db_session):
    source = Source(
        code="dcinside",
        name="DCInside",
        source_type=SourceType.COMMUNITY,
        country="KR",
        base_url="https://gall.dcinside.com",
        is_official=False,
        compliance_notes="test",
        metadata_json={},
    )
    db_session.add(source)
    db_session.flush()
    db_session.add(
        CommunityPost(
            source_id=source.id,
            board_name="미국 주식 마이너 갤러리",
            external_post_id="stockus:1",
            title="테러 발언 테스트",
            body="공격적인 표현이 포함된 본문 테스트",
            created_at=datetime(2026, 3, 11, tzinfo=timezone.utc),
            author_hash=None,
            view_count=10,
            upvotes=1,
            downvotes=None,
            comment_count=0,
            original_url="https://example.local/post/1",
            raw_payload={},
        )
    )
    db_session.commit()

    response = api_client.get("/api/v1/community/posts?board_id=stockus")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["analysis"]["hate_index"] >= 0
    assert "market_bias" in payload["items"][0]["analysis"]


def test_refresh_live_community_endpoint(api_client, monkeypatch):
    def fake_collect_live(self, db, board_ids=None, max_pages=None, max_posts=None):
        assert board_ids == ["stockus"]
        assert max_pages == 1
        assert max_posts == 5
        return CollectorResult(
            name="dcinside",
            records_processed=2,
            message="Stored 2 DCInside posts across 1 galleries.",
        )

    monkeypatch.setattr(DCInsideConnector, "collect_live", fake_collect_live)

    response = api_client.post("/api/v1/community/refresh-live?board_id=stockus&max_pages=1&max_posts=5")

    assert response.status_code == 200
    payload = response.json()
    assert payload["board_id"] == "stockus"
    assert payload["records_processed"] == 2
