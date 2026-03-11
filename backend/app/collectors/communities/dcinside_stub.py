from __future__ import annotations

from app.collectors.base.contracts import CollectorResult
from app.collectors.communities.base import BaseCommunityConnector


class DCInsideDisabledConnector(BaseCommunityConnector):
    connector_name = "dcinside_disabled"
    enabled = False
    compliance_note = (
        "Disabled by default. Review robots.txt, terms of service, and legal constraints before implementation."
    )

    def fetch_board_metadata(self) -> dict:
        return {"status": "disabled", "reason": self.compliance_note}

    def fetch_posts_page(self) -> list[dict]:
        return []

    def fetch_post_detail(self, post_stub: dict) -> dict:
        return post_stub

    def parse_post(self, payload: dict) -> dict:
        return payload

    def normalize_post(self, parsed: dict):
        raise RuntimeError("DCInside connector is intentionally disabled pending compliance review.")

    def collect(self, db) -> CollectorResult:
        return CollectorResult(name=self.connector_name, message=self.compliance_note)
