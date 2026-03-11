from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.analytics.rule_based import RuleBasedAnalysisEngine
from app.models.reference import DocumentTag
from app.models.sentiment import Sentiment
from app.services.content_filters import classify_market_post


class AnalysisService:
    def __init__(self) -> None:
        self.engine = RuleBasedAnalysisEngine()

    def analyze_document(
        self, db: Session, document_type: str, document_id: int, title: str, body: str | None
    ) -> Sentiment:
        result = self.engine.analyze(title=title, body=body)
        classification = (
            classify_market_post(title, body) if document_type == "community_post" else None
        )
        existing = db.scalar(
            select(Sentiment).where(
                Sentiment.document_type == document_type,
                Sentiment.document_id == document_id,
            )
        )
        if existing is None:
            existing = Sentiment(
                document_type=document_type,
                document_id=document_id,
                sentiment_score=result.sentiment_score,
                fear_greed_score=result.fear_greed_score,
                hate_index=result.hate_index,
                uncertainty_score=result.uncertainty_score,
                market_bias=result.market_bias,
                labels=result.labels,
                keywords=result.keywords,
                analysis_metadata={
                    "entities": result.entities,
                    "topics": result.topics,
                    "analytics_excluded": classification.excluded if classification else False,
                    "exclusion_reasons": classification.reasons if classification else [],
                },
            )
            db.add(existing)
            db.flush()
        else:
            existing.sentiment_score = result.sentiment_score
            existing.fear_greed_score = result.fear_greed_score
            existing.hate_index = result.hate_index
            existing.uncertainty_score = result.uncertainty_score
            existing.market_bias = result.market_bias
            existing.labels = result.labels
            existing.keywords = result.keywords
            existing.analysis_metadata = {
                "entities": result.entities,
                "topics": result.topics,
                "analytics_excluded": classification.excluded if classification else False,
                "exclusion_reasons": classification.reasons if classification else [],
            }

        db.execute(
            delete(DocumentTag).where(
                DocumentTag.document_type == document_type,
                DocumentTag.document_id == document_id,
            )
        )
        for keyword in result.keywords:
            db.add(
                DocumentTag(
                    document_type=document_type,
                    document_id=document_id,
                    tag_type="keyword",
                    tag_value=keyword,
                    score=1.0,
                )
            )
        for entity in result.entities:
            db.add(
                DocumentTag(
                    document_type=document_type,
                    document_id=document_id,
                    tag_type="entity",
                    tag_value=entity,
                    score=1.0,
                )
            )
        for topic in result.topics:
            db.add(
                DocumentTag(
                    document_type=document_type,
                    document_id=document_id,
                    tag_type="topic",
                    tag_value=topic,
                    score=1.0,
                )
            )
        if classification:
            db.add(
                DocumentTag(
                    document_type=document_type,
                    document_id=document_id,
                    tag_type="content_class",
                    tag_value="excluded" if classification.excluded else "opinion",
                    score=1.0,
                )
            )
        return existing
