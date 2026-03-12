from __future__ import annotations

from dataclasses import dataclass

from app.analytics.lexicons import (
    ENTITY_PATTERNS,
    FEAR_WORDS,
    GREED_WORDS,
    HATE_OR_AGGRESSION_WORDS,
    INTENSIFIERS,
    NEGATIONS,
    NEGATIVE_WORDS,
    POSITIVE_WORDS,
    STOPWORDS,
    TOPIC_KEYWORDS,
    UNCERTAINTY_WORDS,
)
from app.utils.text import clean_text, tokenize, top_keywords


@dataclass
class AnalysisResult:
    sentiment_score: float
    fear_greed_score: float
    hate_index: float
    uncertainty_score: float
    market_bias: str
    keywords: list[str]
    topics: list[str]
    entities: list[str]


class RuleBasedAnalyzer:
    def analyze(self, title: str, body: str) -> AnalysisResult:
        clean_title = clean_text(title)
        clean_body = clean_text(body)
        title_tokens = tokenize(clean_title)
        body_tokens = tokenize(clean_body)
        combined_tokens = title_tokens + body_tokens

        title_score = self._score_sentiment(title_tokens) * 1.7
        body_score = self._score_sentiment(body_tokens)
        sentiment_score = max(-100.0, min(100.0, (title_score + body_score) * 8))

        fear = sum(token in FEAR_WORDS for token in combined_tokens)
        greed = sum(token in GREED_WORDS for token in combined_tokens)
        fear_greed_score = max(0.0, min(100.0, 50 + (greed - fear) * 9))

        hate_hits = sum(any(term in token for term in HATE_OR_AGGRESSION_WORDS) for token in combined_tokens)
        hate_index = max(0.0, min(100.0, hate_hits * 12.5))

        uncertainty_hits = sum(any(term in token for term in UNCERTAINTY_WORDS) for token in combined_tokens)
        uncertainty_score = max(0.0, min(100.0, uncertainty_hits * 16.0))

        bias = self._derive_market_bias(sentiment_score, fear_greed_score, uncertainty_score)
        keywords = top_keywords(combined_tokens, STOPWORDS, limit=8)
        topics = self._extract_topics(combined_tokens)
        entities = self._extract_entities(combined_tokens)

        return AnalysisResult(
            sentiment_score=round(sentiment_score, 2),
            fear_greed_score=round(fear_greed_score, 2),
            hate_index=round(hate_index, 2),
            uncertainty_score=round(uncertainty_score, 2),
            market_bias=bias,
            keywords=keywords,
            topics=topics,
            entities=entities,
        )

    def _score_sentiment(self, tokens: list[str]) -> float:
        score = 0.0
        for index, token in enumerate(tokens):
            weight = 1.0
            if index > 0 and tokens[index - 1] in INTENSIFIERS:
                weight += 0.5
            if any(neg in token for neg in NEGATIONS):
                weight *= -0.7
            if token in POSITIVE_WORDS:
                score += weight
            if token in NEGATIVE_WORDS:
                score -= weight
        return score

    def _derive_market_bias(
        self, sentiment_score: float, fear_greed_score: float, uncertainty_score: float
    ) -> str:
        composite = sentiment_score + (fear_greed_score - 50) - uncertainty_score * 0.25
        if composite >= 15:
            return "bullish"
        if composite <= -15:
            return "bearish"
        return "neutral"

    def _extract_topics(self, tokens: list[str]) -> list[str]:
        token_set = set(tokens)
        return [topic for topic, keywords in TOPIC_KEYWORDS.items() if token_set & keywords]

    def _extract_entities(self, tokens: list[str]) -> list[str]:
        token_set = set(tokens)
        found: list[str] = []
        for keywords in ENTITY_PATTERNS.values():
            found.extend(sorted(token_set & keywords))
        return found
