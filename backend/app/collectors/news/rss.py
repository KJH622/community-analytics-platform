from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser
from bs4 import BeautifulSoup

from app.collectors.base.base import BaseCollector
from app.collectors.base.types import NormalizedArticle
from app.services.text_cleaner import canonicalize_url, clean_text


logger = logging.getLogger(__name__)


class RssNewsCollector(BaseCollector):
    collector_name = "rss-news"

    def __init__(self, feed_url: str, source_code: str, category: str | None = None) -> None:
        super().__init__()
        self.feed_url = feed_url
        self.source_code = source_code
        self.category = category

    def fetch(self) -> Iterable[NormalizedArticle]:
        content = self.get_text(self.feed_url)
        feed = feedparser.parse(content)
        normalized: list[NormalizedArticle] = []
        for entry in feed.entries:
            article = self._normalize_entry(entry)
            if article:
                normalized.append(article)
        return normalized

    def _normalize_entry(self, entry: Any) -> NormalizedArticle | None:
        url = getattr(entry, "link", None)
        if not url:
            return None
        summary = clean_text(getattr(entry, "summary", None))
        body = self._fetch_body(url) or summary
        published = self._parse_datetime(getattr(entry, "published", None))
        tags = [tag.term for tag in getattr(entry, "tags", [])] if getattr(entry, "tags", None) else None
        return NormalizedArticle(
            source_code=self.source_code,
            title=clean_text(getattr(entry, "title", "")),
            summary=summary or None,
            body=body or None,
            author=getattr(entry, "author", None),
            published_at=published,
            canonical_url=canonicalize_url(url),
            url=url,
            category=self.category,
            tags=tags,
            raw_payload={
                "title": getattr(entry, "title", None),
                "link": url,
                "summary": getattr(entry, "summary", None),
                "published": getattr(entry, "published", None),
                "author": getattr(entry, "author", None),
            },
        )

    def _fetch_body(self, url: str) -> str | None:
        try:
            html = self.get_text(url)
        except Exception as exc:  # pragma: no cover - best effort fetch
            logger.debug("Failed to enrich article body %s: %s", url, exc)
            return None
        soup = BeautifulSoup(html, "html.parser")
        paragraphs = [clean_text(element.get_text(" ")) for element in soup.select("article p, main p")]
        paragraphs = [paragraph for paragraph in paragraphs if paragraph]
        return " ".join(paragraphs[:8]) if paragraphs else None

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return parsedate_to_datetime(value)
        except Exception:
            return None
