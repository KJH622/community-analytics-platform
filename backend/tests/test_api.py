from datetime import date, datetime, timezone

from app.collectors.base.contracts import CollectorResult
from app.collectors.communities.dcinside import DCInsideConnector

from app.models import EconomicIndicator, IndicatorRelease
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
