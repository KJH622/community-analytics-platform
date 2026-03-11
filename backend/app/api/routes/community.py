from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.analytics.rule_based import RuleBasedAnalyzer
from app.collectors.communities.dcinside import DCInsideConnector
from app.models import CommunityPost
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
):
    items, total = get_community_posts(
        db,
        page=page,
        page_size=page_size,
        board_name=board_name,
        board_id=board_id,
    )
    return {
        "items": [_serialize_post(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/posts/{post_id}", response_model=CommunityPostRead)
def get_community_post(post_id: int, db: Session = Depends(get_db)):
    post = db.execute(select(CommunityPost).where(CommunityPost.id == post_id)).scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=404, detail="Community post not found")
    return _serialize_post(post)


@router.post("/refresh-live", response_model=dict)
def refresh_live_community_posts(
    db: Session = Depends(get_db),
    board_id: str = Query(default="stockus"),
    max_pages: int = Query(default=1, ge=1, le=3),
    max_posts: int = Query(default=10, ge=1, le=30),
):
    connector = DCInsideConnector()
    result = connector.collect_live(db, board_ids=[board_id], max_pages=max_pages, max_posts=max_posts)
    return {
        "status": "success",
        "board_id": board_id,
        "records_processed": result.records_processed,
        "message": result.message,
    }


def _serialize_post(post: CommunityPost) -> dict:
    payload = CommunityPostRead.model_validate(
        {
            "id": post.id,
            "board_name": post.board_name,
            "title": post.title,
            "body": post.body,
            "created_at": post.created_at,
            "view_count": post.view_count,
            "upvotes": post.upvotes,
            "downvotes": post.downvotes,
            "comment_count": post.comment_count,
            "original_url": post.original_url,
            "analysis": analyzer.analyze(post.title, post.body).__dict__,
        }
    )
    return payload.model_dump()
