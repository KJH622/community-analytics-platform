from datetime import date

from app.models.reference import Source
from app.politics.models.tables import PoliticalIndicator, PoliticalIndicatorValue, Politician


def test_can_insert_core_and_political_models(db_session):
    source = Source(code="mock", name="Mock", kind="community", country="KR", base_url="https://example.com")
    db_session.add(source)
    db_session.add(
        Politician(
            name="이재명",
            party="더불어민주당",
            position="정치인",
            ideology="liberal",
            country="KR",
        )
    )
    indicator = PoliticalIndicator(
        code="KR_PRESIDENT_APPROVAL",
        indicator_name="대통령 지지율",
        country="KR",
        unit="%",
        source="Mock",
    )
    db_session.add(indicator)
    db_session.flush()
    db_session.add(
        PoliticalIndicatorValue(
            indicator_id=indicator.id,
            date=date(2026, 3, 1),
            value=41.2,
            label="overall",
            source="Mock",
            unit="%",
        )
    )
    db_session.commit()

    assert source.id is not None
    assert indicator.values[0].value == 41.2
