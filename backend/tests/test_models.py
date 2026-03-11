from datetime import date, datetime, timezone

from app.models import EconomicIndicator, IndicatorRelease
from app.politics.models import PoliticalIndicator, PoliticalIndicatorValue, Politician


def test_market_models_persist(db_session):
    indicator = EconomicIndicator(
        code="TEST_CPI",
        name="Test CPI",
        country="US",
        category="inflation",
        unit="index",
        frequency="monthly",
        importance=4,
    )
    db_session.add(indicator)
    db_session.flush()
    release = IndicatorRelease(
        indicator_id=indicator.id,
        country="US",
        release_date=date(2026, 3, 1),
        release_time=None,
        actual_value=123.4,
        forecast_value=122.0,
        previous_value=121.0,
        unit="index",
        importance=4,
        source_url="https://example.local",
        released_at=datetime.now(tz=timezone.utc),
        metadata_json={},
    )
    db_session.add(release)
    db_session.commit()

    assert indicator.id is not None
    assert release.id is not None


def test_politics_models_persist(db_session):
    politician = Politician(
        name="테스트 정치인",
        party="테스트당",
        position="후보",
        ideology="center",
        country="KR",
        aliases_json=[],
        metadata_json={},
    )
    indicator = PoliticalIndicator(
        code="approval",
        indicator_name="지지율",
        country="KR",
        unit="%",
        source="sample",
        metadata_json={},
    )
    db_session.add_all([politician, indicator])
    db_session.flush()
    value = PoliticalIndicatorValue(
        indicator_id=indicator.id,
        date=date(2026, 3, 11),
        value=44.2,
        label="테스트 정치인",
        source="sample",
        unit="%",
    )
    db_session.add(value)
    db_session.commit()

    assert politician.id is not None
    assert value.id is not None
