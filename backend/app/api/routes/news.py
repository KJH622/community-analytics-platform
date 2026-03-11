from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import Article
from app.schemas.news import ArticleRead
from app.services.query import get_news

router = APIRouter(prefix="/api/v1/news", tags=["news"])


@router.get("", response_model=dict)
def list_news(
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: str | None = None,
):
    items, total = get_news(db, page=page, page_size=page_size, keyword=keyword)
    return {
        "items": [
            {
                "id": item.id,
                "title": item.title,
                "body": item.body,
                "publisher": item.publisher,
                "canonical_url": item.canonical_url,
                "category": item.category,
                "tags": item.tags_json,
                "published_at": item.published_at,
            }
            for item in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{article_id}", response_model=ArticleRead)
def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.execute(select(Article).where(Article.id == article_id)).scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return ArticleRead(
        id=article.id,
        title=article.title,
        body=article.body,
        publisher=article.publisher,
        canonical_url=article.canonical_url,
        category=article.category,
        tags=article.tags_json,
        published_at=article.published_at,
    )
