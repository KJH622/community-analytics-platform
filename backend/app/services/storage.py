from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.collectors.base.types import (
    NormalizedArticle,
    NormalizedCommunityComment,
    NormalizedCommunityPost,
    NormalizedIndicatorRelease,
)
from app.models.article import Article
from app.models.community import CommunityComment, CommunityPost
from app.models.indicator import EconomicIndicator, IndicatorRelease
from app.models.reference import Source, SourceConnector
from app.services.article_clustering import assign_article_cluster
from app.services.text_cleaner import canonicalize_url, clean_text
from app.utils.hashing import sha256_hexdigest
from app.utils.json import to_jsonable


def get_or_create_source(
    db: Session,
    *,
    code: str,
    name: str,
    kind: str,
    country: str | None,
    base_url: str | None,
    enabled: bool = True,
    robots_policy: str | None = None,
    tos_notes: str | None = None,
) -> Source:
    source = db.scalar(select(Source).where(Source.code == code))
    if source is None:
        source = Source(
            code=code,
            name=name,
            kind=kind,
            country=country,
            base_url=base_url,
            enabled=enabled,
            robots_policy=robots_policy,
            tos_notes=tos_notes,
        )
        db.add(source)
        db.flush()
    return source


def ensure_source_connector(
    db: Session,
    source: Source,
    *,
    connector_type: str,
    status: str,
    schedule_hint: str | None,
    rate_limit_per_minute: int,
    legal_notes: str | None = None,
) -> SourceConnector:
    connector = db.scalar(
        select(SourceConnector).where(
            SourceConnector.source_id == source.id,
            SourceConnector.connector_type == connector_type,
        )
    )
    if connector is None:
        connector = SourceConnector(
            source_id=source.id,
            connector_type=connector_type,
            status=status,
            is_enabled=status == "active",
            schedule_hint=schedule_hint,
            rate_limit_per_minute=rate_limit_per_minute,
            legal_notes=legal_notes,
        )
        db.add(connector)
        db.flush()
    return connector


def upsert_indicator_release(db: Session, source: Source, payload: NormalizedIndicatorRelease) -> int:
    indicator = db.scalar(select(EconomicIndicator).where(EconomicIndicator.code == payload.indicator.code))
    if indicator is None:
        indicator = EconomicIndicator(
            source_id=source.id,
            code=payload.indicator.code,
            name=payload.indicator.name,
            country=payload.indicator.country,
            category=payload.indicator.category,
            unit=payload.indicator.unit,
            frequency=payload.indicator.frequency,
            description=payload.indicator.description,
            source_url=payload.indicator.source_url,
            next_release_at=payload.indicator.next_release_at,
        )
        db.add(indicator)
        db.flush()
    existing = db.scalar(
        select(IndicatorRelease).where(
            IndicatorRelease.indicator_id == indicator.id,
            IndicatorRelease.release_date == payload.release_date,
        )
    )
    if existing:
        existing.actual_value = payload.actual_value
        existing.forecast_value = payload.forecast_value
        existing.previous_value = payload.previous_value
        existing.release_time = payload.release_time
        existing.unit = payload.unit
        existing.importance = payload.importance
        existing.source_url = payload.source_url
        return existing.id

    release = IndicatorRelease(
        indicator_id=indicator.id,
        country=payload.country,
        release_date=payload.release_date,
        release_time=payload.release_time,
        actual_value=payload.actual_value,
        forecast_value=payload.forecast_value,
        previous_value=payload.previous_value,
        unit=payload.unit,
        importance=payload.importance,
        source_url=payload.source_url,
    )
    db.add(release)
    db.flush()
    return release.id


def upsert_article(db: Session, source: Source, payload: NormalizedArticle) -> tuple[Article, bool]:
    canonical_url = canonicalize_url(payload.canonical_url)
    cleaned_body = clean_text(payload.body)
    content_hash = sha256_hexdigest(f"{payload.title}::{cleaned_body}")
    existing = db.scalar(
        select(Article).where(
            Article.source_id == source.id,
            Article.canonical_url == canonical_url,
        )
    )
    if existing:
        existing.title = payload.title
        existing.summary = clean_text(payload.summary)
        existing.body = cleaned_body or None
        existing.author = payload.author
        existing.published_at = payload.published_at
        existing.url = payload.url
        existing.category = payload.category
        existing.tags = payload.tags
        existing.content_hash = content_hash
        existing.raw_payload = to_jsonable(payload.raw_payload)
        return existing, False

    article = Article(
        source_id=source.id,
        title=payload.title,
        summary=clean_text(payload.summary) or None,
        body=cleaned_body or None,
        author=payload.author,
        published_at=payload.published_at,
        canonical_url=canonical_url,
        url=payload.url,
        category=payload.category,
        tags=payload.tags,
        content_hash=content_hash,
        raw_payload=to_jsonable(payload.raw_payload),
    )
    db.add(article)
    db.flush()
    assign_article_cluster(db, article)
    return article, True


def upsert_community_post(
    db: Session, source: Source, payload: NormalizedCommunityPost
) -> tuple[CommunityPost, bool]:
    content_hash = sha256_hexdigest(f"{payload.title}::{clean_text(payload.body)}")
    author_hash = sha256_hexdigest(payload.author_identifier) if payload.author_identifier else None
    existing = db.scalar(
        select(CommunityPost).where(
            CommunityPost.source_id == source.id,
            CommunityPost.external_id == payload.external_id,
        )
    )
    if existing:
        _apply_post(existing, payload, author_hash, content_hash)
        return existing, False

    post = CommunityPost(
        source_id=source.id,
        board_name=payload.board_name,
        external_id=payload.external_id,
        title=payload.title,
        body=clean_text(payload.body) or None,
        published_at=payload.published_at,
        author_hash=author_hash,
        view_count=payload.view_count,
        upvotes=payload.upvotes,
        downvotes=payload.downvotes,
        comment_count=payload.comment_count,
        url=payload.url,
        content_hash=content_hash,
        raw_payload=to_jsonable(payload.raw_payload),
    )
    db.add(post)
    db.flush()
    _replace_comments(db, post, payload.comments)
    return post, True


def _apply_post(
    post: CommunityPost,
    payload: NormalizedCommunityPost,
    author_hash: str | None,
    content_hash: str,
) -> None:
    post.board_name = payload.board_name
    post.title = payload.title
    post.body = clean_text(payload.body) or None
    post.published_at = payload.published_at
    post.author_hash = author_hash
    post.view_count = payload.view_count
    post.upvotes = payload.upvotes
    post.downvotes = payload.downvotes
    post.comment_count = payload.comment_count
    post.url = payload.url
    post.content_hash = content_hash
    post.raw_payload = to_jsonable(payload.raw_payload)


def _replace_comments(
    db: Session, post: CommunityPost, comments: list[NormalizedCommunityComment]
) -> None:
    post.comments.clear()
    db.flush()
    for comment in comments:
        post.comments.append(
            CommunityComment(
                external_id=comment.external_id,
                body=clean_text(comment.body),
                published_at=comment.published_at,
                author_hash=(
                    sha256_hexdigest(comment.author_identifier)
                    if comment.author_identifier
                    else None
                ),
                upvotes=comment.upvotes,
                downvotes=comment.downvotes,
                content_hash=sha256_hexdigest(comment.body),
                raw_payload=to_jsonable(comment.raw_payload),
            )
        )
