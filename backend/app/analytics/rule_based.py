from __future__ import annotations

from pathlib import Path

from app.analytics.base import AnalysisResult, BaseAnalysisEngine
from app.analytics.entity_topic import extract_entities_and_topics
from app.analytics.keywords import extract_keywords, tokenize


NEGATIONS = {"안", "못", "없", "아니", "not", "no", "never"}
EMPHASIS_TOKENS = {"진짜", "완전", "매우", "엄청", "개", "초", "너무"}


def _load_terms(filename: str) -> set[str]:
    path = Path(__file__).resolve().parent / "lexicons" / filename
    with open(path, "r", encoding="utf-8") as file:
        return {
            line.strip().lower()
            for line in file
            if line.strip() and not line.strip().startswith("#")
        }


POSITIVE_TERMS = _load_terms("positive_terms.txt")
NEGATIVE_TERMS = _load_terms("negative_terms.txt")
FEAR_TERMS = _load_terms("fear_terms.txt")
GREED_TERMS = _load_terms("greed_terms.txt")
UNCERTAINTY_TERMS = _load_terms("uncertainty_terms.txt")
HATE_TERMS = _load_terms("hate_terms.txt")


class RuleBasedAnalysisEngine(BaseAnalysisEngine):
    def analyze(self, title: str, body: str | None = None) -> AnalysisResult:
        full_body = body or ""
        combined_text = f"{title} {full_body}".strip()
        title_tokens = tokenize(title)
        body_tokens = tokenize(full_body)

        sentiment_score = self._sentiment(title_tokens, body_tokens)
        fear_greed_score = self._fear_greed(title_tokens, body_tokens)
        hate_index = self._hate_index(title_tokens, body_tokens, combined_text)
        uncertainty_score = self._uncertainty(title_tokens, body_tokens, combined_text)
        market_bias = self._market_bias(
            sentiment_score=sentiment_score,
            fear_greed_score=fear_greed_score,
            uncertainty_score=uncertainty_score,
        )
        keywords = extract_keywords(combined_text)
        entity_topic = extract_entities_and_topics(combined_text)

        labels = []
        if fear_greed_score <= 35:
            labels.append("fear")
        if fear_greed_score >= 65:
            labels.append("greed")
        if hate_index >= 40:
            labels.append("toxicity")
        if uncertainty_score >= 45:
            labels.append("uncertain")

        return AnalysisResult(
            sentiment_score=sentiment_score,
            fear_greed_score=fear_greed_score,
            hate_index=hate_index,
            uncertainty_score=uncertainty_score,
            market_bias=market_bias,
            labels=labels,
            keywords=keywords,
            entities=entity_topic.entities,
            topics=entity_topic.topics,
        )

    def _sentiment(self, title_tokens: list[str], body_tokens: list[str]) -> float:
        title_score = self._scored_term_balance(title_tokens, POSITIVE_TERMS, NEGATIVE_TERMS)
        body_score = self._scored_term_balance(body_tokens, POSITIVE_TERMS, NEGATIVE_TERMS)
        score = (title_score * 1.6) + body_score
        return max(-100.0, min(100.0, score * 12.0))

    def _fear_greed(self, title_tokens: list[str], body_tokens: list[str]) -> float:
        fear = self._term_hits(title_tokens, FEAR_TERMS) * 1.5 + self._term_hits(body_tokens, FEAR_TERMS)
        greed = self._term_hits(title_tokens, GREED_TERMS) * 1.5 + self._term_hits(body_tokens, GREED_TERMS)
        score = 50.0 + (greed - fear) * 8.0
        return max(0.0, min(100.0, score))

    def _hate_index(self, title_tokens: list[str], body_tokens: list[str], text: str) -> float:
        hits = self._term_hits(title_tokens, HATE_TERMS) * 1.4 + self._term_hits(body_tokens, HATE_TERMS)
        punctuation_boost = min(text.count("!") * 2.0, 12.0)
        sarcasm_boost = 6.0 if "ㅋㅋ" in text or "lol" in text.lower() else 0.0
        score = min(100.0, hits * 14.0 + punctuation_boost + sarcasm_boost)
        return score

    def _uncertainty(self, title_tokens: list[str], body_tokens: list[str], text: str) -> float:
        hits = self._term_hits(title_tokens, UNCERTAINTY_TERMS) * 1.3 + self._term_hits(
            body_tokens, UNCERTAINTY_TERMS
        )
        punctuation_boost = min(text.count("?") * 3.0, 15.0)
        score = min(100.0, hits * 10.0 + punctuation_boost)
        return score

    def _market_bias(
        self, sentiment_score: float, fear_greed_score: float, uncertainty_score: float
    ) -> str:
        if sentiment_score >= 20 and fear_greed_score >= 55 and uncertainty_score < 60:
            return "bullish"
        if sentiment_score <= -20 and fear_greed_score <= 45:
            return "bearish"
        return "neutral"

    def _scored_term_balance(
        self, tokens: list[str], positive_terms: set[str], negative_terms: set[str]
    ) -> float:
        score = 0.0
        for index, token in enumerate(tokens):
            emphasis = 1.4 if index > 0 and tokens[index - 1] in EMPHASIS_TOKENS else 1.0
            window = tokens[max(0, index - 2) : index]
            negated = any(any(window_token.startswith(neg) for neg in NEGATIONS) for window_token in window)
            if token in positive_terms:
                score += -1.0 * emphasis if negated else 1.0 * emphasis
            elif token in negative_terms:
                score += 1.0 * emphasis if negated else -1.0 * emphasis
        return score

    def _term_hits(self, tokens: list[str], lexicon: set[str]) -> float:
        return float(sum(1 for token in tokens if token in lexicon))
