from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.collectors.communities.dcinside import DCInsideConnector
from app.models import CommunityPost
from app.schemas.community import (
    CommunityPostAnalysisRead,
    CommunityPostAnalysisRequest,
    CommunityPostRead,
    MarketSummaryRead,
    MarketSummaryRequest,
)
from app.services.community_analysis import CommunityAnalysisService
from app.services.market_summary import MarketSummaryService
from app.services.query import get_community_posts

router = APIRouter(prefix="/api/v1/community", tags=["community"])
analysis_service = CommunityAnalysisService()
market_summary_service = MarketSummaryService()


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


@router.post("/analyze", response_model=CommunityPostAnalysisRead)
def analyze_community_post(payload: CommunityPostAnalysisRequest):
    return CommunityPostAnalysisRead.model_validate(analysis_service.analyze_text(payload.title, payload.body).__dict__)


@router.post("/market-summary", response_model=MarketSummaryRead)
def generate_market_summary(payload: MarketSummaryRequest):
    return MarketSummaryRead.model_validate(market_summary_service.generate(payload.model_dump()))


@router.post("/reanalyze-all", response_model=dict)
def reanalyze_all_community_posts(db: Session = Depends(get_db)):
    processed = analysis_service.backfill_all_posts(db)
    return {"status": "success", "records_processed": processed}


@router.post("/reanalyze-recent", response_model=dict)
def reanalyze_recent_community_posts(
    db: Session = Depends(get_db),
    limit: int = Query(default=30, ge=1, le=30),
    board_name: str | None = None,
):
    processed = analysis_service.backfill_recent_posts(db, limit=limit, board_name=board_name)
    return {"status": "success", "records_processed": processed, "limit": limit, "board_name": board_name}


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
    stored_analysis = analysis_service.read_stored_analysis(post)
    analysis = stored_analysis or analysis_service.analyze_text(post.title, post.body).__dict__
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
            "analysis": analysis,
        }
    )
    return payload.model_dump()
