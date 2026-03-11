from collections import Counter
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.politics.models.tables import (
    PoliticalDailySnapshot,
    PoliticalIndicator,
    PoliticalPost,
    PoliticalSentiment,
    Politician,
)
from app.politics.schemas.api import (
    KeywordPoint,
    PolarizationPoint,
    PoliticalIndicatorRead,
    PoliticalPostRead,
    PoliticalSentimentRead,
    PoliticalSnapshotRead,
    PoliticianRead,
    PoliticsDashboardResponse,
)
from app.politics.services.reference import POLITICAL_COMMUNITY_REFERENCES
from app.services.content_filters import classify_political_post, compute_political_influence_score


router = APIRouter(prefix="/api/v1/politics", tags=["politics"])


@router.get("/dashboard", response_model=PoliticsDashboardResponse)
def politics_dashboard(db: Session = Depends(get_db)) -> PoliticsDashboardResponse:
    latest_snapshot = db.scalar(
        select(PoliticalDailySnapshot).order_by(PoliticalDailySnapshot.snapshot_date.desc())
    )
    indicators = db.scalars(
        select(PoliticalIndicator)
        .options(selectinload(PoliticalIndicator.values))
        .order_by(PoliticalIndicator.indicator_name)
    ).all()
    filtered_posts = _load_filtered_political_posts(db, days=3)

    politician_counter = Counter()
    keyword_counter = Counter()
    for post, _, _ in filtered_posts:
        for entity in post.entities:
            if entity.entity_type == "politician":
                politician_counter[entity.name] += entity.mention_count
            elif entity.entity_type == "keyword":
                keyword_counter[entity.name] += entity.mention_count

    posts = [
        _serialize_political_post(post, sentiment, classification)
        for post, sentiment, classification in filtered_posts[:10]
    ]

    return PoliticsDashboardResponse(
        sentiment_snapshot=(
            PoliticalSnapshotRead.model_validate(latest_snapshot) if latest_snapshot else None
        ),
        indicators=[PoliticalIndicatorRead.model_validate(item) for item in indicators],
        top_politicians=[
            KeywordPoint(keyword=name, count=count)
            for name, count in politician_counter.most_common(10)
        ],
        keyword_trends=[
            KeywordPoint(keyword=name, count=count)
            for name, count in keyword_counter.most_common(10)
        ],
        posts=posts,
        community_references=POLITICAL_COMMUNITY_REFERENCES,
    )


@router.get("/politicians", response_model=list[PoliticianRead])
def list_politicians(db: Session = Depends(get_db)) -> list[PoliticianRead]:
    rows = db.scalars(select(Politician).order_by(Politician.name)).all()
    return [PoliticianRead.model_validate(row) for row in rows]


@router.get("/politicians/{name}", response_model=PoliticianRead)
def get_politician(name: str, db: Session = Depends(get_db)) -> PoliticianRead:
    row = db.scalar(select(Politician).where(Politician.name == name))
    if row is None:
        raise HTTPException(status_code=404, detail="Politician not found")
    return PoliticianRead.model_validate(row)


@router.get("/indicators", response_model=list[PoliticalIndicatorRead])
def list_political_indicators(db: Session = Depends(get_db)) -> list[PoliticalIndicatorRead]:
    rows = db.scalars(
        select(PoliticalIndicator)
        .options(selectinload(PoliticalIndicator.values))
        .order_by(PoliticalIndicator.indicator_name)
    ).all()
    return [PoliticalIndicatorRead.model_validate(row) for row in rows]


@router.get("/keywords", response_model=list[KeywordPoint])
def political_keywords(db: Session = Depends(get_db)) -> list[KeywordPoint]:
    filtered_posts = _load_filtered_political_posts(db, days=3)
    counter = Counter()
    for post, _, _ in filtered_posts:
        for entity in post.entities:
            if entity.entity_type == "keyword":
                counter[entity.name] += entity.mention_count
    return [KeywordPoint(keyword=name, count=count) for name, count in counter.most_common(20)]


@router.get("/community-posts", response_model=list[PoliticalPostRead])
def political_posts(
    limit: int = Query(default=20, le=100),
    date_from: date | None = None,
    db: Session = Depends(get_db),
) -> list[PoliticalPostRead]:
    days = 3 if date_from is None else max((date.today() - date_from).days + 1, 1)
    rows = _load_filtered_political_posts(db, days=days)
    return [_serialize_political_post(post, sentiment, classification) for post, sentiment, classification in rows[:limit]]


@router.get("/sentiment", response_model=list[PoliticalSentimentRead])
def political_sentiment(db: Session = Depends(get_db)) -> list[PoliticalSentimentRead]:
    rows = _load_filtered_political_posts(db, days=3)
    serialized = []
    for _, sentiment, _ in rows:
        if sentiment is not None:
            serialized.append(PoliticalSentimentRead.model_validate(sentiment))
    return serialized[:50]


@router.get("/polarization", response_model=list[PolarizationPoint])
def political_polarization(
    date_from: date | None = None,
    db: Session = Depends(get_db),
) -> list[PolarizationPoint]:
    if date_from is None:
        date_from = date.today() - timedelta(days=2)
    rows = db.execute(
        select(
            PoliticalDailySnapshot.snapshot_date,
            PoliticalDailySnapshot.political_polarization_index,
            PoliticalDailySnapshot.election_heat_index,
        )
        .where(PoliticalDailySnapshot.snapshot_date >= date_from)
        .order_by(PoliticalDailySnapshot.snapshot_date)
    ).all()
    return [
        PolarizationPoint(
            date=row.snapshot_date,
            value=row.political_polarization_index,
            election_heat=row.election_heat_index,
        )
        for row in rows
    ]


def _load_filtered_political_posts(
    db: Session,
    *,
    days: int,
) -> list[tuple[PoliticalPost, PoliticalSentiment | None, object]]:
    date_from = date.today() - timedelta(days=max(days - 1, 0))
    posts = db.scalars(
        select(PoliticalPost)
        .options(selectinload(PoliticalPost.sentiment), selectinload(PoliticalPost.entities))
        .where(PoliticalPost.published_at.is_not(None))
        .where(PoliticalPost.published_at >= datetime.combine(date_from, time.min))
        .order_by(PoliticalPost.published_at.desc())
    ).all()
    if not posts:
        posts = db.scalars(
            select(PoliticalPost)
            .options(selectinload(PoliticalPost.sentiment), selectinload(PoliticalPost.entities))
            .order_by(PoliticalPost.published_at.desc())
            .limit(50)
        ).all()

    rows = []
    for post in posts:
        classification = classify_political_post(post.title, post.body)
        if classification.excluded:
            continue
        rows.append((post, post.sentiment, classification))

    rows.sort(
        key=lambda item: compute_political_influence_score(
            sentiment=item[1],
            title=item[0].title,
            body=item[0].body,
            view_count=item[0].view_count,
            upvotes=item[0].upvotes,
            comment_count=item[0].comment_count,
            published_at=item[0].published_at,
        ),
        reverse=True,
    )
    return rows


def _serialize_political_post(
    post: PoliticalPost,
    sentiment: PoliticalSentiment | None,
    classification,
) -> PoliticalPostRead:
    return PoliticalPostRead(
        id=post.id,
        community_name=post.community_name,
        board_name=post.board_name,
        title=post.title,
        body=post.body,
        published_at=post.published_at,
        view_count=post.view_count,
        upvotes=post.upvotes,
        comment_count=post.comment_count,
        url=post.url,
        political_sentiment_score=sentiment.political_sentiment_score if sentiment else None,
        political_polarization_index=sentiment.political_polarization_index if sentiment else None,
        analytics_excluded=classification.excluded,
        exclusion_reasons=classification.reasons,
        influence_score=compute_political_influence_score(
            sentiment=sentiment,
            title=post.title,
            body=post.body,
            view_count=post.view_count,
            upvotes=post.upvotes,
            comment_count=post.comment_count,
            published_at=post.published_at,
        ),
    )
