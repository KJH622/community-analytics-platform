from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.community import CommunityPost
from app.models.reference import DocumentTag, Source
from app.models.sentiment import Sentiment
from app.schemas.community import CommunityPostListResponse, CommunityPostRead
from app.services.content_filters import classify_market_post, compute_market_influence_score


router = APIRouter()


@router.get("/posts", response_model=CommunityPostListResponse)
def list_community_posts(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    date_from: date | None = None,
    date_to: date | None = None,
    source: str | None = None,
    country: str | None = None,
    topic: str | None = None,
    sentiment: str | None = None,
    exclude_notice_like: bool = Query(default=True),
    sort: str = Query(default="recent", pattern="^(recent|influence)$"),
    db: Session = Depends(get_db),
) -> CommunityPostListResponse:
    query = select(CommunityPost).join(Source, Source.id == CommunityPost.source_id)
    if source:
        source_codes = [item.strip() for item in source.split(",") if item.strip()]
        if len(source_codes) == 1:
            query = query.where(Source.code == source_codes[0])
        elif source_codes:
            query = query.where(Source.code.in_(source_codes))
    if country:
        query = query.where(Source.country == country.upper())
    if date_from:
        query = query.where(CommunityPost.published_at >= datetime.combine(date_from, time.min))
    if date_to:
        query = query.where(CommunityPost.published_at <= datetime.combine(date_to, time.max))
    if topic:
        query = query.join(
            DocumentTag,
            (DocumentTag.document_type == "community_post")
            & (DocumentTag.document_id == CommunityPost.id),
        ).where(DocumentTag.tag_type == "topic", DocumentTag.tag_value == topic)

    posts = db.scalars(query.order_by(CommunityPost.published_at.desc())).unique().all()
    if not posts:
        return CommunityPostListResponse(items=[], total=0)

    sentiment_rows = db.scalars(
        select(Sentiment).where(
            Sentiment.document_type == "community_post",
            Sentiment.document_id.in_([post.id for post in posts]),
        )
    ).all()
    sentiment_map = {item.document_id: item for item in sentiment_rows}

    items: list[CommunityPostRead] = []
    for post in posts:
        sentiment_row = sentiment_map.get(post.id)
        classification = classify_market_post(post.title, post.body)

        if sentiment == "positive" and (sentiment_row is None or sentiment_row.sentiment_score < 0):
            continue
        if sentiment == "negative" and (sentiment_row is None or sentiment_row.sentiment_score >= 0):
            continue
        if exclude_notice_like and classification.excluded:
            continue

        items.append(
            CommunityPostRead(
                id=post.id,
                source_id=post.source_id,
                board_name=post.board_name,
                external_id=post.external_id,
                title=post.title,
                body=post.body,
                published_at=post.published_at,
                author_hash=post.author_hash,
                view_count=post.view_count,
                upvotes=post.upvotes,
                downvotes=post.downvotes,
                comment_count=post.comment_count,
                url=post.url,
                sentiment_score=sentiment_row.sentiment_score if sentiment_row else None,
                fear_greed_score=sentiment_row.fear_greed_score if sentiment_row else None,
                hate_index=sentiment_row.hate_index if sentiment_row else None,
                uncertainty_score=sentiment_row.uncertainty_score if sentiment_row else None,
                market_bias=sentiment_row.market_bias if sentiment_row else None,
                analytics_excluded=classification.excluded,
                exclusion_reasons=classification.reasons,
                influence_score=compute_market_influence_score(
                    sentiment=sentiment_row,
                    title=post.title,
                    body=post.body,
                    view_count=post.view_count,
                    upvotes=post.upvotes,
                    comment_count=post.comment_count,
                    published_at=post.published_at,
                ),
            )
        )

    if sort == "influence":
        items.sort(
            key=lambda item: (
                item.influence_score or 0.0,
                item.published_at.timestamp() if item.published_at else 0.0,
            ),
            reverse=True,
        )
    else:
        items.sort(
            key=lambda item: item.published_at.timestamp() if item.published_at else 0.0,
            reverse=True,
        )

    total = len(items)
    return CommunityPostListResponse(items=items[offset : offset + limit], total=total)


@router.get("/posts/{post_id}", response_model=CommunityPostRead)
def get_community_post(post_id: int, db: Session = Depends(get_db)) -> CommunityPostRead:
    post = db.get(CommunityPost, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Community post not found")
    sentiment_row = db.scalar(
        select(Sentiment).where(
            Sentiment.document_type == "community_post",
            Sentiment.document_id == post.id,
        )
    )
    classification = classify_market_post(post.title, post.body)
    return CommunityPostRead(
        id=post.id,
        source_id=post.source_id,
        board_name=post.board_name,
        external_id=post.external_id,
        title=post.title,
        body=post.body,
        published_at=post.published_at,
        author_hash=post.author_hash,
        view_count=post.view_count,
        upvotes=post.upvotes,
        downvotes=post.downvotes,
        comment_count=post.comment_count,
        url=post.url,
        sentiment_score=sentiment_row.sentiment_score if sentiment_row else None,
        fear_greed_score=sentiment_row.fear_greed_score if sentiment_row else None,
        hate_index=sentiment_row.hate_index if sentiment_row else None,
        uncertainty_score=sentiment_row.uncertainty_score if sentiment_row else None,
        market_bias=sentiment_row.market_bias if sentiment_row else None,
        analytics_excluded=classification.excluded,
        exclusion_reasons=classification.reasons,
        influence_score=compute_market_influence_score(
            sentiment=sentiment_row,
            title=post.title,
            body=post.body,
            view_count=post.view_count,
            upvotes=post.upvotes,
            comment_count=post.comment_count,
            published_at=post.published_at,
        ),
    )
