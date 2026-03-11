from datetime import date, datetime, timezone

from app.models.article import Article
from app.models.community import CommunityPost
from app.models.reference import Source
from app.models.sentiment import DailyMarketSentimentSnapshot, Sentiment
from app.politics.models.tables import (
    PoliticalDailySnapshot,
    PoliticalEntity,
    PoliticalIndicator,
    PoliticalIndicatorValue,
    PoliticalPost,
    PoliticalSentiment,
    Politician,
)


def seed_market_data(db_session):
    source = Source(
        code="nasdaq_markets",
        name="Nasdaq Markets",
        kind="news",
        country="US",
        base_url="https://www.nasdaq.com/",
    )
    community_source = Source(
        code="mock_community",
        name="Mock Community",
        kind="community",
        country="KR",
        base_url="https://community.local/",
    )
    db_session.add_all([source, community_source])
    db_session.flush()

    article = Article(
        source_id=source.id,
        title="Stocks rally after CPI",
        summary="Markets rise",
        body="Risk appetite improved after CPI release.",
        published_at=datetime(2026, 3, 11, tzinfo=timezone.utc),
        canonical_url="https://example.com/news/1",
        url="https://example.com/news/1",
        category="markets",
        tags=["cpi"],
        content_hash="hash-1",
    )
    post = CommunityPost(
        source_id=community_source.id,
        board_name="국내주식",
        external_id="p1",
        title="코스피 반등",
        body="공포는 있지만 반등 기대도 있다.",
        published_at=datetime(2026, 3, 11, tzinfo=timezone.utc),
        url="https://community.local/posts/1",
        content_hash="hash-2",
    )
    snapshot = DailyMarketSentimentSnapshot(
        snapshot_key="2026-03-11::all::all::all",
        snapshot_date=date(2026, 3, 11),
        source_kind="all",
        country="all",
        topic_code="all",
        sentiment_avg=12.5,
        fear_greed_avg=58.4,
        hate_index_avg=14.2,
        uncertainty_avg=33.0,
        bullish_ratio=0.5,
        bearish_ratio=0.2,
        neutral_ratio=0.3,
        article_count=1,
        community_post_count=1,
        top_keywords=["cpi", "rally"],
    )
    db_session.add_all([article, post, snapshot])
    db_session.flush()
    db_session.add_all(
        [
            Sentiment(
                document_type="article",
                document_id=article.id,
                sentiment_score=44,
                fear_greed_score=62,
                hate_index=5,
                uncertainty_score=12,
                market_bias="bullish",
                labels=["greed"],
                keywords=["cpi", "rally"],
            ),
            Sentiment(
                document_type="community_post",
                document_id=post.id,
                sentiment_score=6,
                fear_greed_score=49,
                hate_index=8,
                uncertainty_score=30,
                market_bias="neutral",
                labels=["uncertain"],
                keywords=["코스피", "반등"],
            ),
        ]
    )
    db_session.commit()


def seed_politics_data(db_session):
    politician = Politician(
        name="이재명",
        party="더불어민주당",
        position="정치인",
        ideology="liberal",
        country="KR",
    )
    indicator = PoliticalIndicator(
        code="KR_PRESIDENT_APPROVAL",
        indicator_name="대통령 지지율",
        country="KR",
        unit="%",
        source="Mock",
    )
    db_session.add_all([politician, indicator])
    db_session.flush()
    db_session.add(
        PoliticalIndicatorValue(
            indicator_id=indicator.id,
            date=date(2026, 3, 1),
            value=39.8,
            label="overall",
            source="Mock",
            unit="%",
        )
    )
    post = PoliticalPost(
        source_id=None,
        community_name="정치토론 커뮤니티",
        board_name="대선 게시판",
        external_id="pol-1",
        title="이재명 후보 지지와 반대가 엇갈린다",
        body="대선 열기는 높고 지지층은 열광, 반대층은 분노한다.",
        published_at=datetime(2026, 3, 11, tzinfo=timezone.utc),
        url="https://politics.local/posts/1",
    )
    db_session.add(post)
    db_session.flush()
    db_session.add(
        PoliticalSentiment(
            post_id=post.id,
            political_sentiment_score=8,
            support_score=44,
            opposition_score=32,
            anger_score=20,
            sarcasm_score=8,
            apathy_score=2,
            enthusiasm_score=28,
            political_polarization_index=37,
            election_heat_index=61,
            labels=["support", "anger"],
            keywords=["이재명", "대선"],
        )
    )
    db_session.add(
        PoliticalEntity(
            post_id=post.id,
            entity_type="politician",
            name="이재명",
            canonical_name="이재명",
            mention_count=2,
            score=2.0,
        )
    )
    db_session.add(
        PoliticalDailySnapshot(
            snapshot_date=date(2026, 3, 11),
            political_sentiment_avg=8.0,
            political_polarization_index=37.0,
            election_heat_index=61.0,
            top_keywords=["대선", "이재명"],
            top_politicians=["이재명"],
            post_count=1,
        )
    )
    db_session.commit()


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_market_endpoints(client, db_session):
    seed_market_data(db_session)

    news_response = client.get("/api/v1/news")
    sentiment_response = client.get("/api/v1/analytics/daily-sentiment")

    assert news_response.status_code == 200
    assert news_response.json()["total"] == 1
    assert sentiment_response.status_code == 200
    assert sentiment_response.json()[0]["fear_greed_avg"] == 58.4


def test_politics_dashboard_and_lists(client, db_session):
    seed_politics_data(db_session)

    dashboard = client.get("/api/v1/politics/dashboard")
    politicians = client.get("/api/v1/politics/politicians")
    polarization = client.get("/api/v1/politics/polarization")

    assert dashboard.status_code == 200
    assert dashboard.json()["sentiment_snapshot"]["political_polarization_index"] == 37.0
    assert politicians.status_code == 200
    assert politicians.json()[0]["name"] == "이재명"
    assert polarization.status_code == 200
    assert polarization.json()[0]["value"] == 37.0
