from datetime import datetime, timezone

from app.models.sentiment import Sentiment
from app.services.content_filters import (
    classify_market_post,
    classify_political_post,
    compute_market_influence_score,
)


def test_classify_market_post_excludes_notice_like_titles():
    result = classify_market_post("📣 휴장일 안내 및 CPI 일정 정리", "이번 주 일정 공유")
    assert result.excluded is True
    assert result.reasons


def test_classify_political_post_keeps_opinion_posts():
    result = classify_political_post("대선 후보 토론 보고 진짜 화난다", "이건 너무 실망스럽다")
    assert result.excluded is False


def test_market_influence_score_rewards_emotional_recent_posts():
    sentiment = Sentiment(
        document_type="community_post",
        document_id=1,
        sentiment_score=-48,
        fear_greed_score=22,
        hate_index=41,
        uncertainty_score=35,
        market_bias="bearish",
        labels=["fear"],
        keywords=["폭락"],
    )
    score = compute_market_influence_score(
        sentiment=sentiment,
        title="오늘 진짜 폭락장이다",
        body="다들 패닉와서 손절한다",
        view_count=1200,
        upvotes=55,
        comment_count=24,
        published_at=datetime.now(timezone.utc),
    )
    assert score > 0
