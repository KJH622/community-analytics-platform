from datetime import datetime, timezone
import json
from pathlib import Path

from app.collectors.communities.dcinside import DCInsideConnector
from app.models import CommunityPost


LIST_HTML = """
<table>
  <tbody>
    <tr class="ub-content">
      <td class="gall_num">101</td>
      <td class="gall_subject">일반</td>
      <td class="gall_tit ub-word">
        <a href="/mgallery/board/view/?id=stockus&no=101&page=1">첫 번째 글</a>
        <a class="reply_numbox">[3]</a>
      </td>
      <td class="gall_writer" data-nick="작성자" data-ip="1.2">작성자</td>
      <td class="gall_date" title="2026-03-11 09:00:00">09:00</td>
      <td class="gall_count">15</td>
      <td class="gall_recommend">7</td>
    </tr>
  </tbody>
</table>
"""

DETAIL_HTML = """
<div class="view_content_wrap">
  <span class="title_subject">첫 번째 글</span>
  <div class="gall_writer" data-nick="작성자" data-ip="1.2">작성자</div>
  <span class="gall_date" title="2026-03-11 09:00:00">2026.03.11 09:00:00</span>
  <span class="gall_count">조회 15</span>
  <span class="gall_reply_num">추천 7</span>
  <div class="write_div">본문 내용입니다.</div>
</div>
"""


class DummyResponse:
    def __init__(self, text: str) -> None:
        self.text = text


def test_dcinside_connector_collects_posts(db_session, monkeypatch):
    connector = DCInsideConnector()
    connector.settings.community_max_pages_per_board = 1
    connector.settings.community_max_posts_per_board = 1

    def fake_get(url: str, **kwargs):
        if "board/lists" in url:
            return DummyResponse(LIST_HTML)
        return DummyResponse(DETAIL_HTML)

    monkeypatch.setattr(connector, "get", fake_get)

    result = connector.collect(db_session)

    assert result.records_processed == 3
    stored = db_session.query(CommunityPost).all()
    assert len(stored) == 3
    assert stored[0].title == "첫 번째 글"
    assert stored[0].body == "본문 내용입니다."
    assert stored[0].comment_count == 3
    assert stored[0].upvotes == 7
    assert stored[0].external_post_id == "stockus:101"
    assert stored[0].created_at.replace(tzinfo=timezone.utc) == datetime(2026, 3, 11, 0, 0, tzinfo=timezone.utc)


def test_dcinside_connector_uses_snapshot_fallback(db_session, monkeypatch, tmp_path):
    connector = DCInsideConnector()
    connector.settings.community_max_pages_per_board = 1
    connector.settings.community_max_posts_per_board = 1
    connector.snapshot_dir = tmp_path

    snapshot_row = [
        {
            "gallery_id": "stockus",
            "post_no": 777,
            "title": "스냅샷 제목",
            "author": "스냅유저",
            "datetime": "2026-03-11 12:34:56",
            "url": "https://gall.dcinside.com/mgallery/board/view/?id=stockus&no=777&page=1",
        }
    ]
    (tmp_path / "stockus.json").write_text(json.dumps(snapshot_row, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "jusik.json").write_text("[]", encoding="utf-8")
    (tmp_path / "kospi.json").write_text("[]", encoding="utf-8")

    def fake_get(url: str, **kwargs):
        if "board/lists" in url:
            return DummyResponse("")
        return DummyResponse(DETAIL_HTML)

    monkeypatch.setattr(connector, "get", fake_get)

    result = connector.collect(db_session)

    assert result.records_processed == 1
    stored = db_session.query(CommunityPost).all()
    assert len(stored) == 1
    assert stored[0].external_post_id == "stockus:777"
    assert stored[0].title == "첫 번째 글"
