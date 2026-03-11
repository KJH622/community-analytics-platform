from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.analytics import (
    CommunityOverviewResponse,
    HourlyComparisonPoint,
    HourlyComparisonResponse,
    KeywordTrendPoint,
    TopicBreakdownPoint,
)
from app.schemas.common import DailySnapshotResponse
from app.services.market_intraday import fetch_intraday_index
from app.services.query import (
    get_daily_sentiment,
    get_community_overview,
    get_hourly_hate_index,
    get_keyword_trends,
    get_topic_breakdown,
)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/daily-sentiment", response_model=list[DailySnapshotResponse])
def daily_sentiment(db: Session = Depends(get_db), limit: int = Query(default=30, ge=1, le=365)):
    snapshots = get_daily_sentiment(db, limit=limit)
    return [
        DailySnapshotResponse(
            snapshot_date=item.snapshot_date,
            country=item.country,
            sentiment_score=item.sentiment_score,
            fear_greed_score=item.fear_greed_score,
            hate_index=item.hate_index,
            uncertainty_score=item.uncertainty_score,
            bullish_ratio=item.bullish_ratio,
            bearish_ratio=item.bearish_ratio,
            neutral_ratio=item.neutral_ratio,
            top_keywords=item.top_keywords_json,
        )
        for item in snapshots
    ]


@router.get("/keyword-trends", response_model=list[KeywordTrendPoint])
def keyword_trends(db: Session = Depends(get_db), limit: int = Query(default=10, ge=1, le=50)):
    return [KeywordTrendPoint(**item) for item in get_keyword_trends(db, limit=limit)]


@router.get("/topic-breakdown", response_model=list[TopicBreakdownPoint])
def topic_breakdown(db: Session = Depends(get_db)):
    return [TopicBreakdownPoint(**item) for item in get_topic_breakdown(db)]


@router.get("/community-overview", response_model=CommunityOverviewResponse)
def community_overview(
    db: Session = Depends(get_db),
    days: int = Query(default=7, ge=1, le=30),
    board_name: str | None = Query(default=None),
):
    return CommunityOverviewResponse(**get_community_overview(db, days=days, board_name=board_name))


@router.get("/hourly-comparison", response_model=HourlyComparisonResponse)
def hourly_comparison(
    db: Session = Depends(get_db),
    hours: int = Query(default=24, ge=6, le=72),
    board_name: str | None = Query(default=None),
):
    hate_points = get_hourly_hate_index(db, hours=hours, board_name=board_name)

    try:
        kospi_points = fetch_intraday_index("%5EKS11", limit=hours)
    except Exception:
        kospi_points = []

    try:
        nasdaq_points = fetch_intraday_index("%5EIXIC", limit=hours)
    except Exception:
        nasdaq_points = []

    kospi_by_label = {item["label"]: item for item in kospi_points}
    nasdaq_by_label = {item["label"]: item for item in nasdaq_points}

    first_kospi = next((item["value"] for item in kospi_points if item.get("value") is not None), None)
    first_nasdaq = next((item["value"] for item in nasdaq_points if item.get("value") is not None), None)

    points = []
    for point in hate_points:
        label = point["label"]
        kospi = kospi_by_label.get(label)
        nasdaq = nasdaq_by_label.get(label)
        kospi_value = float(kospi["value"]) if kospi and kospi.get("value") is not None else None
        nasdaq_value = float(nasdaq["value"]) if nasdaq and nasdaq.get("value") is not None else None

        points.append(
            HourlyComparisonPoint(
                timestamp=point["timestamp"],
                label=label,
                hate_index=point["hate_index"],
                post_count=point["post_count"],
                kospi_value=kospi_value,
                kospi_change_pct=round(((kospi_value - first_kospi) / first_kospi) * 100, 2)
                if kospi_value is not None and first_kospi
                else None,
                nasdaq_value=nasdaq_value,
                nasdaq_change_pct=round(((nasdaq_value - first_nasdaq) / first_nasdaq) * 100, 2)
                if nasdaq_value is not None and first_nasdaq
                else None,
            )
        )

    return HourlyComparisonResponse(timezone="Asia/Seoul", board_name=board_name, points=points)
