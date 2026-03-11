from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import feedparser
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.collectors.base.contracts import BaseCollector, CollectorResult
from app.models import Article, ArticleCluster, Source, SourceType
from app.utils.hashing import sha256_text
from app.utils.text import clean_text

RSS_SOURCES = {
    "marketwatch_topstories": {
        "name": "MarketWatch Top Stories",
        "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
        "publisher": "MarketWatch",
        "country": "US",
        "category": "markets",
    },
    "cnbc_markets": {
        "name": "CNBC Markets",
        "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "publisher": "CNBC",
        "country": "US",
        "category": "markets",
    },
}


class RssNewsCollector(BaseCollector):
    def collect(self, db: Session) -> CollectorResult:
        processed = 0
        for code, meta in RSS_SOURCES.items():
            source = db.execute(select(Source).where(Source.code == code)).scalar_one_or_none()
            if source is None:
                source = Source(
                    code=code,
                    name=meta["name"],
                    source_type=SourceType.NEWS,
                    country=meta["country"],
                    base_url=meta["url"],
                    is_official=False,
                    compliance_notes="RSS source. Respect publisher copyright and feed usage terms.",
                )
                db.add(source)
                db.flush()

            feed = feedparser.parse(meta["url"])
            for entry in feed.entries[:20]:
                canonical_url = getattr(entry, "link", None)
                if not canonical_url:
                    continue
                exists = db.execute(
                    select(Article).where(Article.canonical_url == canonical_url)
                ).scalar_one_or_none()
                if exists:
                    continue
                title = clean_text(getattr(entry, "title", ""))
                summary = clean_text(getattr(entry, "summary", ""))
                body_hash = sha256_text(summary)
                title_hash = sha256_text(title)
                cluster_key = sha256_text(title.lower()[:80])
                cluster = db.execute(
                    select(ArticleCluster).where(ArticleCluster.cluster_key == cluster_key)
                ).scalar_one_or_none()
                if cluster is None:
                    cluster = ArticleCluster(cluster_key=cluster_key, topic_label=title[:120])
                    db.add(cluster)
                    db.flush()

                db.add(
                    Article(
                        source_id=source.id,
                        cluster_id=cluster.id,
                        title=title,
                        body=summary,
                        summary=summary,
                        author=getattr(entry, "author", None),
                        publisher=meta["publisher"],
                        canonical_url=canonical_url,
                        original_url=canonical_url,
                        language="en",
                        category=meta["category"],
                        tags_json=self._entry_tags(entry),
                        title_hash=title_hash,
                        body_hash=body_hash,
                        published_at=self._parse_published_at(entry),
                        raw_payload={"domain": urlparse(canonical_url).netloc},
                    )
                )
                processed += 1
        db.commit()
        return CollectorResult(name="rss_news", records_processed=processed, message=f"Stored {processed} news items.")

    def _parse_published_at(self, entry) -> datetime:
        if getattr(entry, "published", None):
            return parsedate_to_datetime(entry.published).astimezone(timezone.utc)
        return datetime.now(tz=timezone.utc)

    def _entry_tags(self, entry) -> list[str]:
        return [tag.term for tag in getattr(entry, "tags", []) if getattr(tag, "term", None)]
