from datetime import datetime

from pydantic import BaseModel


class ArticleRead(BaseModel):
    id: int
    title: str
    body: str
    publisher: str | None
    canonical_url: str
    category: str | None
    tags: list[str]
    published_at: datetime

    model_config = {"from_attributes": True}
