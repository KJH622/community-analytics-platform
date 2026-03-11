from __future__ import annotations

from collections.abc import Iterable

from app.collectors.communities.dcinside_connector import DcInsideConnector, DcInsideGalleryConfig
from app.politics.collectors.base import BasePoliticalCommunityConnector, NormalizedPoliticalPost


class DcInsidePoliticalConnector(BasePoliticalCommunityConnector):
    collector_name = "dcinside-political-gallery"

    def __init__(
        self,
        gallery_id: str,
        board_name: str,
        limit: int = 12,
        max_pages: int = 1,
    ) -> None:
        super().__init__()
        self.connector = DcInsideConnector(
            DcInsideGalleryConfig(
                gallery_id=gallery_id,
                board_name=board_name,
                community_name="디시인사이드",
                limit=limit,
                max_pages=max_pages,
            )
        )

    def fetch_posts(self) -> Iterable[NormalizedPoliticalPost]:
        rows = []
        for post in self.connector.fetch():
            rows.append(
                NormalizedPoliticalPost(
                    source_code=f"dcinside_{self.connector.config.gallery_id}_politics",
                    community_name="디시인사이드",
                    board_name=self.connector.config.board_name,
                    external_id=post.external_id,
                    title=post.title,
                    body=post.body,
                    published_at=post.published_at,
                    view_count=post.view_count,
                    upvotes=post.upvotes,
                    comment_count=post.comment_count,
                    url=post.url,
                    raw_payload=post.raw_payload,
                )
            )
        return rows
