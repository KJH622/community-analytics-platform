from datetime import datetime

from app.schemas.common import ORMModel


class ArticleRead(ORMModel):
    id: int
    title: str
    summary: str | None
    body: str | None
    author: str | None
    published_at: datetime | None
    canonical_url: str
    url: str
    category: str | None
    tags: list[str] | None
    source_id: int
    cluster_id: int | None


class ArticleListResponse(ORMModel):
    items: list[ArticleRead]
    total: int
