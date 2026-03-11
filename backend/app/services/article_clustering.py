from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.article import Article, ArticleCluster
from app.services.deduplication import similarity
from app.utils.hashing import sha256_hexdigest


def assign_article_cluster(db: Session, article: Article) -> None:
    if article.published_at is None:
        return
    window_start = article.published_at - timedelta(days=1)
    candidates = db.scalars(
        select(Article).where(
            Article.id != article.id,
            Article.published_at >= window_start,
            Article.published_at <= article.published_at + timedelta(days=1),
        )
    ).all()
    for candidate in candidates:
        if similarity(article.title, candidate.title) >= 0.88:
            if candidate.cluster_id:
                article.cluster_id = candidate.cluster_id
                return
            cluster = ArticleCluster(
                cluster_key=sha256_hexdigest(f"{candidate.title.lower()}::{candidate.published_at.date()}")[:24],
                topic=candidate.category,
                representative_title=candidate.title,
                centroid_terms=candidate.tags or [],
            )
            db.add(cluster)
            db.flush()
            candidate.cluster_id = cluster.id
            article.cluster_id = cluster.id
            return

    cluster_key = sha256_hexdigest(
        f"{article.title.lower()}::{(article.published_at or datetime.now(timezone.utc)).date()}"
    )[:24]
    cluster = ArticleCluster(
        cluster_key=cluster_key,
        topic=article.category,
        representative_title=article.title,
        centroid_terms=article.tags or [],
    )
    db.add(cluster)
    db.flush()
    article.cluster_id = cluster.id
