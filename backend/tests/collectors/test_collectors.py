from app.collectors.communities.mock_connector import MockCommunityConnector
from app.politics.collectors.mock_sources import (
    MockPoliticalCommunityConnector,
    MockPoliticalIndicatorCollector,
)


def test_mock_community_connector_loads_fixture():
    posts = list(MockCommunityConnector().fetch())
    assert posts
    assert posts[0].board_name


def test_mock_political_collectors_load_fixtures():
    posts = list(MockPoliticalCommunityConnector().fetch())
    indicators = MockPoliticalIndicatorCollector().fetch()

    assert len(posts) >= 2
    assert any(item.indicator_code == "KR_PRESIDENT_APPROVAL" for item in indicators)
