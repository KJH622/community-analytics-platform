from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.analytics.rule_based import RuleBasedAnalyzer
from app.models import CommunityPost, Sentiment
from app.schemas.community import CommunityPostRead
from app.services.query import get_community_posts

router = APIRouter(prefix="/api/v1/community", tags=["community"])
analyzer = RuleBasedAnalyzer()


@router.get("/posts", response_model=dict)
def list_community_posts(
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    board_name: str | None = None,
    board_id: str | None = None,
    source_code: str | None = None,
    topic_category: str | None = Query(default=None, pattern="^(economy|politics)$"),
):
    items, total = get_community_posts(
        db,
        page=page,
        page_size=page_size,
        board_name=board_name,
        board_id=board_id,
        source_code=source_code,
        topic_category=topic_category,
    )
    sentiment_map = _load_sentiment_map(db, [item.id for item in items])
    return {
        "items": [_serialize_post(item, sentiment_map.get(item.id)) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/posts/{post_id}", response_model=CommunityPostRead)
def get_community_post(post_id: int, db: Session = Depends(get_db)):
    post = db.execute(select(CommunityPost).where(CommunityPost.id == post_id)).scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=404, detail="Community post not found")
    sentiment = db.execute(
        select(Sentiment).where(
            Sentiment.document_type == "community_post",
            Sentiment.document_id == post.id,
        )
    ).scalar_one_or_none()
    return _serialize_post(post, sentiment)


def _serialize_post(post: CommunityPost, sentiment: Sentiment | None = None) -> dict:
    analysis = (
        {
            "sentiment_score": sentiment.sentiment_score,
            "fear_greed_score": sentiment.fear_greed_score,
            "hate_index": sentiment.hate_index,
            "uncertainty_score": sentiment.uncertainty_score,
            "market_bias": sentiment.market_bias,
            "keywords": sentiment.keywords_json,
            "topics": sentiment.topics_json,
            "entities": sentiment.entities_json,
        }
        if sentiment is not None
        else analyzer.analyze(post.title, post.body).__dict__
    )
    payload = CommunityPostRead.model_validate(
        {
            "id": post.id,
            "source_code": getattr(post.source, "code", None) or post.raw_payload.get("source_code"),
            "source_name": getattr(post.source, "name", None) or post.raw_payload.get("source_name"),
            "board_code": post.board_code,
            "board_name": post.board_name,
            "topic_category": post.topic_category,
            "title": post.title,
            "body": post.body,
            "created_at": post.created_at,
            "author_hash": post.author_hash,
            "view_count": post.view_count,
            "upvotes": post.upvotes,
            "downvotes": post.downvotes,
            "comment_count": post.comment_count,
            "original_url": post.original_url,
            "analysis": analysis,
        }
    )
    return payload.model_dump()


def _load_sentiment_map(db: Session, post_ids: list[int]) -> dict[int, Sentiment]:
    if not post_ids:
        return {}
    sentiments = db.execute(
        select(Sentiment).where(
            Sentiment.document_type == "community_post",
            Sentiment.document_id.in_(post_ids),
        )
    ).scalars().all()
    return {item.document_id: item for item in sentiments}
