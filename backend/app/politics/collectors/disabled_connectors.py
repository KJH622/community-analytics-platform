from __future__ import annotations

from collections.abc import Iterable

from app.collectors.base.exceptions import DisabledConnectorError
from app.politics.collectors.base import BasePoliticalCommunityConnector, NormalizedPoliticalPost


class DisabledPoliticalCommunityConnector(BasePoliticalCommunityConnector):
    collector_name = "disabled-political-community"

    def __init__(self, site_name: str, legal_note: str) -> None:
        super().__init__()
        self.site_name = site_name
        self.legal_note = legal_note

    def fetch_posts(self) -> Iterable[NormalizedPoliticalPost]:
        raise DisabledConnectorError(
            f"{self.site_name} connector is disabled until robots.txt and terms review is complete: {self.legal_note}"
        )
