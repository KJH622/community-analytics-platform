from datetime import date, datetime, timedelta, timezone

from app.collectors.base.contracts import CollectorResult
from app.collectors.communities.dcinside import DCInsideConnector

from app.models import CommunityPost, EconomicIndicator, IndicatorRelease, Sentiment, Source, SourceType
from app.services.query import KST
from app.politics.models import (
    PoliticalCommunitySource,
    PoliticalDailySnapshot,
    PoliticalIndicator,
    PoliticalIndicatorValue,
    PoliticalPost,
    PoliticalSentiment,
    Politician,
)


def seed_market(db_session):
    indicator = EconomicIndicator(
        code="CPI_TEST",
        name="CPI Test",
        country="US",
        category="inflation",
        unit="index",
        frequency="monthly",
        importance=5,
    )
    db_session.add(indicator)
    db_session.flush()
    db_session.add(
        IndicatorRelease(
            indicator_id=indicator.id,
            country="US",
            release_date=date(2026, 3, 1),
            release_time=None,
            actual_value=300.1,
            forecast_value=299.8,
            previous_value=298.7,
            unit="index",
            importance=5,
            source_url="https://example.local/cpi",
            released_at=datetime.now(tz=timezone.utc),
            metadata_json={},
        )
    )
    db_session.commit()


def seed_politics(db_session):
    db_session.add(
        Politician(
            name="김민준",
            party="가상여당",
            position="대통령",
            ideology="centrist",
            country="KR",
            aliases_json=["민준 대통령"],
            metadata_json={},
        )
    )
    indicator = PoliticalIndicator(
        code="president_approval",
        indicator_name="대통령 지지율",
        country="KR",
        unit="%",
        source="sample",
        metadata_json={},
    )
    db_session.add(indicator)
    db_session.flush()
    db_session.add(
        PoliticalIndicatorValue(
            indicator_id=indicator.id,
            date=date(2026, 3, 11),
            value=47.1,
            label="대통령",
            source="sample",
            unit="%",
        )
    )
    post = PoliticalPost(
        source_code="mock",
        community_name="Mock Political Forum",
        board_name="election-room",
        external_post_id="1",
        title="대선 분위기 과열",
        body="대선 후보 지지와 반대가 강하게 충돌한다",
        created_at=datetime.now(tz=timezone.utc),
        view_count=120,
        upvotes=12,
        comment_count=7,
        original_url="https://example.local/p/1",
        raw_payload={},
    )
    source = PoliticalCommunitySource(
        code="mock-source",
        name="Mock Political Forum",
        description="mock",
        leaning="unknown",
        link="https://example.local",
        board_name="election-room",
        status="mock",
        compliance_notes="mock",
        metadata_json={},
    )
    db_session.add_all([post, source])
    db_session.flush()
    db_session.add(
        PoliticalSentiment(
            post_id=post.id,
            political_sentiment_score=-10.0,
            support_score=20.0,
            opposition_score=30.0,
            anger_score=15.0,
            mockery_score=0.0,
            political_hate_score=0.0,
            apathy_score=0.0,
            enthusiasm_score=10.0,
            political_polarization_index=40.0,
            election_heat_index=55.0,
            politician_mentions_json=["김민준"],
            keywords_json=["대선", "후보"],
            labels_json=["반대"],
        )
    )
    db_session.add(
        PoliticalDailySnapshot(
            snapshot_date=date(2026, 3, 11),
            country="KR",
            political_sentiment_score=-10.0,
            political_polarization_index=40.0,
            election_heat_index=55.0,
            top_keywords_json=["대선"],
            top_politicians_json=["김민준"],
            source_counts_json={"posts": 1},
        )
    )
    db_session.commit()


def test_health_endpoint(api_client):
    response = api_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_indicator_latest_endpoint(api_client, db_session):
    seed_market(db_session)
    response = api_client.get("/api/v1/indicators/latest")
    assert response.status_code == 200
    assert response.json()[0]["code"] == "CPI_TEST"


def test_hourly_comparison_endpoint(api_client, db_session, monkeypatch):
    source = Source(
        code="dcinside",
        name="DCInside",
        source_type=SourceType.COMMUNITY,
        country="KR",
        base_url="https://gall.dcinside.com",
        is_official=False,
        is_active=True,
        compliance_notes=None,
        metadata_json={},
    )
    db_session.add(source)
    db_session.flush()

    now = datetime.now(tz=timezone.utc).replace(minute=0, second=0, microsecond=0)
    for index, hate_index in enumerate((22.0, 44.0), start=1):
        created_at = now - timedelta(hours=2 - index)
        post = CommunityPost(
            source_id=source.id,
            board_name="stockus-concept",
            external_post_id=f"stockus:{index}",
            title=f"post {index}",
            body="sample body",
            created_at=created_at,
            author_hash=f"author-{index}",
            view_count=10,
            upvotes=1,
            downvotes=0,
            comment_count=0,
            original_url=f"https://example.local/posts/{index}",
            raw_payload={},
        )
        db_session.add(post)
        db_session.flush()
        db_session.add(
            Sentiment(
                document_type="community_post",
                document_id=post.id,
                sentiment_score=0.0,
                fear_greed_score=50.0,
                hate_index=hate_index,
                uncertainty_score=10.0,
                market_bias="neutral",
                keywords_json=[],
                entities_json=[],
                topics_json=[],
            )
        )

    db_session.commit()

    fake_market_points = [
        {
            "timestamp": (now - timedelta(hours=1)).astimezone(timezone(timedelta(hours=9))).isoformat(),
            "label": (now - timedelta(hours=1)).astimezone(KST).strftime("%m-%d %H:00"),
            "value": 100.0,
        },
        {
            "timestamp": now.astimezone(timezone(timedelta(hours=9))).isoformat(),
            "label": now.astimezone(KST).strftime("%m-%d %H:00"),
            "value": 101.0,
        },
    ]

    monkeypatch.setattr(
        "app.api.routes.analytics.fetch_intraday_index",
        lambda symbol, limit=24: fake_market_points,
    )

    response = api_client.get("/api/v1/analytics/hourly-comparison?hours=2&board_name=stockus-concept")
    assert response.status_code == 422

    response = api_client.get("/api/v1/analytics/hourly-comparison?hours=6&board_name=stockus-concept")
    assert response.status_code == 200
    payload = response.json()
    assert payload["timezone"] == "Asia/Seoul"
    assert payload["board_name"] == "stockus-concept"
    assert len(payload["points"]) == 6
    assert payload["points"][-1]["nasdaq_change_pct"] == 1.0


def test_hourly_comparison_averages_hate_index_per_hour(api_client, db_session, monkeypatch):
    source = Source(
        code="dcinside",
        name="DCInside",
        source_type=SourceType.COMMUNITY,
        country="KR",
        base_url="https://gall.dcinside.com",
        is_official=False,
        is_active=True,
        compliance_notes=None,
        metadata_json={},
    )
    db_session.add(source)
    db_session.flush()

    now = datetime.now(tz=timezone.utc).replace(minute=0, second=0, microsecond=0)
    created_at = now - timedelta(hours=1)

    for index, hate_index in enumerate((10.0, 25.5), start=1):
        post = CommunityPost(
            source_id=source.id,
            board_name="stockus-concept",
            external_post_id=f"stockus:sum-{index}",
            title=f"sum post {index}",
            body="sample body",
            created_at=created_at,
            author_hash=f"sum-author-{index}",
            view_count=10,
            upvotes=1,
            downvotes=0,
            comment_count=0,
            original_url=f"https://example.local/posts/sum-{index}",
            raw_payload={},
        )
        db_session.add(post)
        db_session.flush()
        db_session.add(
            Sentiment(
                document_type="community_post",
                document_id=post.id,
                sentiment_score=0.0,
                fear_greed_score=50.0,
                hate_index=hate_index,
                uncertainty_score=10.0,
                market_bias="neutral",
                keywords_json=[],
                entities_json=[],
                topics_json=[],
            )
        )

    db_session.commit()

    fake_market_points = [
        {
            "timestamp": created_at.astimezone(timezone(timedelta(hours=9))).isoformat(),
            "label": created_at.astimezone(KST).strftime("%m-%d %H:00"),
            "value": 100.0,
        },
        {
            "timestamp": now.astimezone(timezone(timedelta(hours=9))).isoformat(),
            "label": now.astimezone(KST).strftime("%m-%d %H:00"),
            "value": 101.0,
        },
    ]

    monkeypatch.setattr(
        "app.api.routes.analytics.fetch_intraday_index",
        lambda symbol, limit=24: fake_market_points,
    )

    response = api_client.get("/api/v1/analytics/hourly-comparison?hours=6&board_name=stockus-concept")

    assert response.status_code == 200
    payload = response.json()
    latest_non_empty_point = next(point for point in reversed(payload["points"]) if point["post_count"] == 2)
    assert latest_non_empty_point["hate_index"] == 17.75


def test_politics_dashboard_endpoint(api_client, db_session):
    seed_politics(db_session)
    response = api_client.get("/api/v1/politics/dashboard")
    assert response.status_code == 200
    payload = response.json()
    assert payload["indicator_cards"][0]["code"] == "president_approval"
    assert payload["reference_communities"][0]["name"] == "Mock Political Forum"


def test_politicians_endpoint(api_client, db_session):
    seed_politics(db_session)
    response = api_client.get("/api/v1/politics/politicians")
    assert response.status_code == 200
    assert response.json()[0]["name"] == "김민준"
