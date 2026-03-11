from datetime import datetime, timezone

from app.collectors.base.contracts import CollectorResult
from app.collectors.communities.dcinside import DCInsideConnector
from app.models import CommunityPost, Source, SourceType
from app.services.market_summary import MarketSummaryService


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


def test_reanalyze_all_community_posts_persists_analysis(api_client, db_session):
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
    post = CommunityPost(
        source_id=source.id,
        board_name="stockus-concept",
        external_post_id="stockus:2",
        title="진짜 역겹다 다 망해라",
        body="이딴 글 쓰는 애들 때문에 커뮤니티가 쓰레기 됐다",
        created_at=datetime(2026, 3, 11, tzinfo=timezone.utc),
        author_hash=None,
        view_count=10,
        upvotes=1,
        downvotes=None,
        comment_count=0,
        original_url="https://example.local/post/2",
        raw_payload={},
    )
    db_session.add(post)
    db_session.commit()

    response = api_client.post("/api/v1/community/reanalyze-all")

    assert response.status_code == 200
    payload = response.json()
    assert payload["records_processed"] >= 1

    db_session.refresh(post)
    assert post.raw_payload["analysis"]["hate_index"] > 0
    assert len(post.raw_payload["analysis"]["tags"]) == 2


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


def test_market_summary_endpoint_returns_three_lines(api_client, monkeypatch):
    def fake_generate(self, payload):
        assert payload["hate_index"] == 31
        return {
            "status_label": "WATCH",
            "summary_lines": ["첫 줄", "둘째 줄", "셋째 줄"],
            "analysis_note": "GPT가 시장과 커뮤니티 분위기를 함께 해석했습니다.",
            "source": "gpt",
        }

    monkeypatch.setattr(MarketSummaryService, "generate", fake_generate)

    response = api_client.post(
        "/api/v1/community/market-summary",
        json={
            "sentiment_score": 12,
            "fear_greed_score": 56,
            "hate_index": 31,
            "uncertainty_score": 18,
            "top_keywords": ["반도체", "cpi"],
            "kospi_value": 2800.12,
            "kospi_change_percent": 0.82,
            "nasdaq_value": 18234.5,
            "nasdaq_change_percent": -0.24,
            "post_count": 10,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status_label"] == "WATCH"
    assert len(payload["summary_lines"]) == 3
