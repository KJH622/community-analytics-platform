from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.politics.schemas.politics import (
    PoliticalCommunitySourceRead,
    PoliticalIndicatorValueRead,
    PoliticalPostRead,
    PoliticalSentimentRead,
    PoliticsDashboardResponse,
    PoliticianRead,
)
from app.politics.services.query import (
    get_dashboard_payload,
    get_political_indicators,
    get_political_keywords,
    get_political_polarization,
    get_political_posts,
    get_political_sentiments,
    get_politician_by_name,
    get_politicians,
)

router = APIRouter(prefix="/api/v1/politics", tags=["politics"])


@router.get("/dashboard", response_model=PoliticsDashboardResponse)
def politics_dashboard(db: Session = Depends(get_db)):
    payload = get_dashboard_payload(db)
    return PoliticsDashboardResponse(
        indicator_cards=[PoliticalIndicatorValueRead(**item) for item in payload["indicator_cards"]],
        approval_trend=[PoliticalIndicatorValueRead(**item) for item in payload["approval_trend"]],
        party_support_comparison=[PoliticalIndicatorValueRead(**item) for item in payload["party_support_comparison"]],
        politician_mentions_top10=payload["politician_mentions_top10"],
        keyword_trends=payload["keyword_trends"],
        political_sentiment_index=payload["political_sentiment_index"],
        polarization_index=payload["polarization_index"],
        election_heat_index=payload["election_heat_index"],
        community_posts=[PoliticalPostRead.model_validate(item) for item in payload["community_posts"]],
        reference_communities=[
            PoliticalCommunitySourceRead(
                name=item.name,
                description=item.description,
                leaning=item.leaning,
                link=item.link,
                status=item.status,
            )
            for item in payload["reference_communities"]
        ],
    )


@router.get("/politicians", response_model=list[PoliticianRead])
def politics_politicians(db: Session = Depends(get_db)):
    return [
        PoliticianRead(
            name=item.name,
            party=item.party,
            position=item.position,
            ideology=item.ideology,
            country=item.country,
            start_term=item.start_term,
            end_term=item.end_term,
            aliases=item.aliases_json,
        )
        for item in get_politicians(db)
    ]


@router.get("/politicians/{name}", response_model=PoliticianRead)
def politics_politician_detail(name: str, db: Session = Depends(get_db)):
    item = get_politician_by_name(db, name)
    if item is None:
        raise HTTPException(status_code=404, detail="Politician not found")
    return PoliticianRead(
        name=item.name,
        party=item.party,
        position=item.position,
        ideology=item.ideology,
        country=item.country,
        start_term=item.start_term,
        end_term=item.end_term,
        aliases=item.aliases_json,
    )


@router.get("/indicators", response_model=list[PoliticalIndicatorValueRead])
def politics_indicators(db: Session = Depends(get_db)):
    return [
        PoliticalIndicatorValueRead(
            indicator_name=indicator.indicator_name,
            code=indicator.code,
            date=value.date,
            value=value.value,
            label=value.label,
            source=value.source,
            unit=value.unit,
        )
        for value, indicator in get_political_indicators(db)
    ]


@router.get("/keywords", response_model=list[dict])
def politics_keywords(db: Session = Depends(get_db)):
    return get_political_keywords(db)


@router.get("/community-posts", response_model=list[PoliticalPostRead])
def politics_community_posts(db: Session = Depends(get_db)):
    return [PoliticalPostRead.model_validate(item) for item in get_political_posts(db)]


@router.get("/sentiment", response_model=list[PoliticalSentimentRead])
def politics_sentiment(db: Session = Depends(get_db)):
    return [
        PoliticalSentimentRead(
            political_sentiment_score=item.political_sentiment_score,
            political_polarization_index=item.political_polarization_index,
            election_heat_index=item.election_heat_index,
            keywords=item.keywords_json,
            labels=item.labels_json,
        )
        for item in get_political_sentiments(db)
    ]


@router.get("/polarization", response_model=list[dict])
def politics_polarization(db: Session = Depends(get_db)):
    return get_political_polarization(db)
