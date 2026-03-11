from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.article import Article
from app.models.reference import DocumentTag, Source
from app.models.sentiment import Sentiment
from app.schemas.news import ArticleListResponse, ArticleRead


router = APIRouter()


@router.get("", response_model=ArticleListResponse)
def list_news(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    date_from: date | None = None,
    date_to: date | None = None,
    source: str | None = None,
    country: str | None = None,
    topic: str | None = None,
    sentiment: str | None = None,
    keyword: str | None = None,
    db: Session = Depends(get_db),
) -> ArticleListResponse:
    query = select(Article).join(Source, Source.id == Article.source_id)
    if source:
        query = query.where(Source.code == source)
    if country:
        query = query.where(Source.country == country.upper())
    if date_from:
        query = query.where(Article.published_at >= datetime.combine(date_from, time.min))
    if date_to:
        query = query.where(Article.published_at <= datetime.combine(date_to, time.max))
    if sentiment == "positive":
        query = query.join(
            Sentiment,
            (Sentiment.document_type == "article") & (Sentiment.document_id == Article.id),
        ).where(Sentiment.sentiment_score >= 0)
    elif sentiment == "negative":
        query = query.join(
            Sentiment,
            (Sentiment.document_type == "article") & (Sentiment.document_id == Article.id),
        ).where(Sentiment.sentiment_score < 0)
    if topic:
        query = query.join(
            DocumentTag,
            (DocumentTag.document_type == "article") & (DocumentTag.document_id == Article.id),
        ).where(DocumentTag.tag_type == "topic", DocumentTag.tag_value == topic)
    if keyword:
        query = query.join(
            DocumentTag,
            (DocumentTag.document_type == "article") & (DocumentTag.document_id == Article.id),
        ).where(DocumentTag.tag_type == "keyword", DocumentTag.tag_value == keyword)

    total = len(db.scalars(query).unique().all())
    items = db.scalars(query.order_by(Article.published_at.desc()).offset(offset).limit(limit)).unique().all()
    return ArticleListResponse(
        items=[ArticleRead.model_validate(item) for item in items],
        total=total,
    )


@router.get("/{article_id}", response_model=ArticleRead)
def get_article(article_id: int, db: Session = Depends(get_db)) -> ArticleRead:
    article = db.get(Article, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return ArticleRead.model_validate(article)
