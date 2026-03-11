from __future__ import annotations

from sqlalchemy import desc
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.analytics.llm_analyzer import LLMCommunityAnalyzer
from app.analytics.rule_based import AnalysisResult, RuleBasedAnalyzer
from app.models import CommunityPost, DocumentTag, Sentiment


class CommunityAnalysisService:
    def __init__(self) -> None:
        self.analyzer = RuleBasedAnalyzer()
        self.llm_analyzer = LLMCommunityAnalyzer()

    def analyze_post(self, post: CommunityPost) -> AnalysisResult:
        return self.analyze_text(post.title, post.body)

    def analyze_text(self, title: str, body: str) -> AnalysisResult:
        if self.llm_analyzer.enabled:
            return self.llm_analyzer.analyze(title, body)
        return self.analyzer.analyze(title, body)

    def persist_post_analysis(self, db: Session, post: CommunityPost) -> AnalysisResult:
        analysis = self.analyze_post(post)
        self._store_analysis_payload(post, analysis)
        self._upsert_sentiment(db, post.id, analysis)
        self._replace_tags(db, post.id, analysis.tags)
        db.flush()
        return analysis

    def backfill_all_posts(self, db: Session) -> int:
        posts = db.execute(select(CommunityPost)).scalars().all()
        for post in posts:
            self.persist_post_analysis(db, post)
        db.commit()
        return len(posts)

    def backfill_recent_posts(self, db: Session, limit: int = 30, board_name: str | None = None) -> int:
        stmt = select(CommunityPost)
        if board_name:
            stmt = stmt.where(CommunityPost.board_name == board_name)
        posts = db.execute(stmt.order_by(desc(CommunityPost.created_at)).limit(limit)).scalars().all()
        for post in posts:
            self.persist_post_analysis(db, post)
        db.commit()
        return len(posts)

    @staticmethod
    def read_stored_analysis(post: CommunityPost) -> dict | None:
        if not post.raw_payload:
            return None
        analysis = post.raw_payload.get("analysis")
        if not isinstance(analysis, dict):
            return None
        return analysis

    def _upsert_sentiment(self, db: Session, post_id: int, analysis: AnalysisResult) -> None:
        sentiment = db.execute(
            select(Sentiment).where(
                Sentiment.document_type == "community_post",
                Sentiment.document_id == post_id,
            )
        ).scalar_one_or_none()
        if sentiment is None:
            sentiment = Sentiment(document_type="community_post", document_id=post_id)
            db.add(sentiment)

        sentiment.sentiment_score = analysis.sentiment_score
        sentiment.fear_greed_score = analysis.fear_greed_score
        sentiment.hate_index = analysis.hate_index
        sentiment.uncertainty_score = analysis.uncertainty_score
        sentiment.market_bias = analysis.market_bias
        sentiment.keywords_json = analysis.keywords
        sentiment.entities_json = analysis.entities
        sentiment.topics_json = analysis.topics

    def _replace_tags(self, db: Session, post_id: int, tags: list[str]) -> None:
        db.execute(
            delete(DocumentTag).where(
                DocumentTag.document_type == "community_post",
                DocumentTag.document_id == post_id,
                DocumentTag.tag_type == "analysis_tag",
            )
        )
        for score, tag in enumerate(tags[::-1], start=1):
            db.add(
                DocumentTag(
                    document_type="community_post",
                    document_id=post_id,
                    tag_type="analysis_tag",
                    tag_value=tag,
                    score=float(len(tags) - score + 1),
                    metadata_json={},
                )
            )

    @staticmethod
    def _store_analysis_payload(post: CommunityPost, analysis: AnalysisResult) -> None:
        raw_payload = dict(post.raw_payload or {})
        raw_payload["analysis"] = {
            "sentiment_score": analysis.sentiment_score,
            "fear_greed_score": analysis.fear_greed_score,
            "hate_score": analysis.hate_score,
            "hate_index": analysis.hate_index,
            "uncertainty_score": analysis.uncertainty_score,
            "market_bias": analysis.market_bias,
            "keywords": analysis.keywords,
            "tags": analysis.tags,
            "topics": analysis.topics,
            "entities": analysis.entities,
        }
        post.raw_payload = raw_payload
