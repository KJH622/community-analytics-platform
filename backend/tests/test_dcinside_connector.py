from datetime import datetime, timezone

from app.collectors.communities.dcinside import DCInsideConnector
from app.models import CommunityPost, Source, SourceType


DESKTOP_EMPTY_HTML = "<html><body></body></html>"

LIST_HTML = """
<table>
  <tbody>
    <tr class="ub-content">
      <td class="gall_num">101</td>
      <td class="gall_subject">일반</td>
      <td class="gall_tit ub-word">
        <a href="/mgallery/board/view/?id=stockus&no=101&page=1">첫번째 글</a>
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
  <span class="title_subject">첫번째 글</span>
  <span class="gall_date" title="2026-03-11 09:00:00">2026.03.11 09:00:00</span>
  <span class="gall_count">조회 15</span>
  <span class="gall_reply_num">추천 7</span>
  <div class="write_div">본문 내용입니다.</div>
</div>
"""

MOBILE_LIST_HTML = """
<ul class="gall-detail-lst">
  <li>
    <div class="gall-detail-lnktb">
      <a class="lt" href="https://m.dcinside.com/board/stockus/101?page=1&recommend=1">
        <span class="subject-add">
          <span class="subjectin">모바일 첫글</span>
        </span>
        <ul class="ginfo">
          <li>일반</li>
          <li>ㅇㅇ</li>
          <li>09:00</li>
          <li>조회 15</li>
          <li class="up-add">추천 <span>7</span></li>
        </ul>
      </a>
      <a class="rt" href="https://m.dcinside.com/board/stockus/101?page=1&recommend=1#comment_box">
        <span class="ct">3</span>
      </a>
    </div>
    <span class="blockInfo" data-name="ㅇㅇ" data-info="abcd1234"></span>
  </li>
</ul>
"""

MOBILE_DETAIL_HTML = """
<div class="gallview-tit-box">
  <span class="tit">[일반] 모바일 첫글</span>
</div>
<ul class="ginfo2">
  <li>ㅇㅇ</li>
  <li>2026.03.11 09:00</li>
  <li>조회수 15</li>
</ul>
<span id="recomm_btn">7</span>
<div class="thum-txtin">모바일 본문 내용입니다.</div>
"""


class DummyResponse:
    def __init__(self, text: str, encoding: str = "utf-8") -> None:
        self.text = text
        self.encoding = encoding
        self.apparent_encoding = encoding


def test_dcinside_connector_collects_desktop_posts(db_session, monkeypatch):
    connector = DCInsideConnector()
    connector.settings.community_max_pages_per_board = 1
    connector.settings.community_max_posts_per_board = 1
    connector.boards = [connector.boards[0]]
    connector.board_name_map = {board["id"]: board["board_name"] for board in connector.boards}

    def fake_get(url: str, **kwargs):
        if "board/lists" in url:
            return DummyResponse(LIST_HTML)
        return DummyResponse(DETAIL_HTML)

    monkeypatch.setattr(connector, "get", fake_get)

    result = connector.collect(db_session)

    assert result.records_processed == 1
    stored = db_session.query(CommunityPost).all()
    assert len(stored) == 1
    assert stored[0].title == "첫번째 글"
    assert stored[0].body == "본문 내용입니다."
    assert stored[0].comment_count == 3
    assert stored[0].upvotes == 7
    assert stored[0].external_post_id == "stockus:101"
    assert stored[0].created_at.replace(tzinfo=timezone.utc) == datetime(2026, 3, 11, 0, 0, tzinfo=timezone.utc)


def test_dcinside_connector_falls_back_to_mobile_html(db_session, monkeypatch):
    connector = DCInsideConnector()
    connector.settings.community_max_pages_per_board = 1
    connector.settings.community_max_posts_per_board = 1
    connector.boards = [connector.boards[0]]
    connector.board_name_map = {board["id"]: board["board_name"] for board in connector.boards}

    def fake_get(url: str, **kwargs):
        if "gall.dcinside.com/mgallery/board/lists" in url:
            return DummyResponse(DESKTOP_EMPTY_HTML)
        return DummyResponse(MOBILE_DETAIL_HTML)

    monkeypatch.setattr(connector, "get", fake_get)
    monkeypatch.setattr(
        connector,
        "get_mobile",
        lambda url, **kwargs: DummyResponse(MOBILE_LIST_HTML)
        if "m.dcinside.com/board/stockus?recommend=1&page=1" in url
        else DummyResponse(MOBILE_DETAIL_HTML),
    )

    result = connector.collect(db_session)

    assert result.records_processed == 1
    stored = db_session.query(CommunityPost).one()
    assert stored.title == "모바일 첫글"
    assert stored.body == "모바일 본문 내용입니다."
    assert stored.comment_count == 3
    assert stored.upvotes == 7
    assert stored.author_hash is not None


def test_dcinside_connector_repairs_mojibake_existing_posts(db_session, monkeypatch):
    connector = DCInsideConnector()
    connector.settings.community_max_pages_per_board = 1
    connector.settings.community_max_posts_per_board = 1
    connector.boards = [connector.boards[0]]
    connector.board_name_map = {board["id"]: board["board_name"] for board in connector.boards}

    source = Source(
        code="dcinside",
        name="DCInside",
        source_type=SourceType.COMMUNITY,
        country="KR",
        base_url="https://gall.dcinside.com",
        is_official=False,
        compliance_notes="test",
        metadata_json={},
    )
    db_session.add(source)
    db_session.flush()
    db_session.add(
        CommunityPost(
            source_id=source.id,
            board_name="stockus-concept",
            external_post_id="stockus:101",
            title="坪什杷研 訊 切荷 恭嬢走虞壱 壱紫走鎧劃壱?",
            body="葛什韓 -50遁 据馬檎鯵蓄 せせせせせせせ",
            created_at=datetime(2026, 3, 11, tzinfo=timezone.utc),
            author_hash=None,
            view_count=1,
            upvotes=1,
            downvotes=None,
            comment_count=0,
            original_url="https://example.local/post/1",
            raw_payload={},
        )
    )
    db_session.commit()

    def fake_get(url: str, **kwargs):
        if "gall.dcinside.com/mgallery/board/lists" in url:
            return DummyResponse(DESKTOP_EMPTY_HTML)
        return DummyResponse(MOBILE_DETAIL_HTML)

    monkeypatch.setattr(connector, "get", fake_get)
    monkeypatch.setattr(
        connector,
        "get_mobile",
        lambda url, **kwargs: DummyResponse(MOBILE_LIST_HTML)
        if "m.dcinside.com/board/stockus?recommend=1&page=1" in url
        else DummyResponse(MOBILE_DETAIL_HTML),
    )

    result = connector.collect(db_session)

    assert result.records_processed == 0
    repaired = db_session.query(CommunityPost).filter_by(external_post_id="stockus:101").one()
    assert repaired.title == "모바일 첫글"
    assert repaired.body == "모바일 본문 내용입니다."
