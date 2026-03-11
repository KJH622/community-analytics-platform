from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from app.analytics.rule_based import AnalysisResult, RuleBasedAnalyzer
from app.core.config import get_settings


SYSTEM_PROMPT = """
You analyze Korean community posts about markets and public sentiment.
Return only valid JSON.

Rules:
- Read title and body together.
- Score hate_score, uncertainty_score, fear_greed_score, hate_index as percentages from 0 to 100.
- fear_greed_score: 0 is extreme fear, 100 is extreme greed, 50 is neutral.
- hate_index should be a composite indicator based on hate, uncertainty, and fear/greed extremity.
- market_bias must be exactly one of: bullish, bearish, neutral.
- tags must contain exactly 2 short Korean tags.
- If the input is Korean, tags, keywords, and entities should also be in Korean unless a proper noun is commonly written in English.
- keywords should contain up to 8 important keywords and should prefer words actually appearing in the post.
- topics should contain broad topic labels in English snake_case style.
- entities should contain important company, country, index, commodity, or policy names.
- Be sensitive to slang, sarcasm, insults, geopolitical risk, and finance jargon.
- Do not return generic placeholder scores. Use the actual text.

JSON schema:
{
  "sentiment_score": number,
  "fear_greed_score": number,
  "hate_score": number,
  "hate_index": number,
  "uncertainty_score": number,
  "market_bias": "bullish" | "bearish" | "neutral",
  "keywords": string[],
  "tags": [string, string],
  "topics": string[],
  "entities": string[]
}
""".strip()


class LLMCommunityAnalyzer:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.rule_based = RuleBasedAnalyzer()
        self.client = (
            OpenAI(
                api_key=self.settings.openai_api_key,
                timeout=self.settings.openai_timeout_seconds,
            )
            if self.settings.openai_api_key
            else None
        )

    @property
    def enabled(self) -> bool:
        return self.client is not None

    def analyze(self, title: str, body: str) -> AnalysisResult:
        if self.client is None:
            return self.rule_based.analyze(title, body)

        response = self.client.responses.create(
            model=self.settings.openai_model,
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": SYSTEM_PROMPT}],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": f"Title:\n{title.strip() or '(empty)'}\n\nBody:\n{body.strip() or '(empty)'}",
                        }
                    ],
                },
            ],
            max_output_tokens=600,
        )
        payload = self._parse_response(getattr(response, "output_text", "") or "")
        return self._normalize_payload(payload, title=title, body=body)

    def _parse_response(self, value: str) -> dict[str, Any]:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            start = value.find("{")
            end = value.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(value[start : end + 1])
            raise

    def _normalize_payload(self, payload: dict[str, Any], title: str, body: str) -> AnalysisResult:
        fallback = self.rule_based.analyze(title, body)

        def clamp_score(key: str, default: float) -> float:
            raw = payload.get(key, default)
            try:
                return round(max(0.0, min(100.0, float(raw))), 2)
            except (TypeError, ValueError):
                return round(default, 2)

        def clamp_sentiment(default: float) -> float:
            raw = payload.get("sentiment_score", default)
            try:
                return round(max(-100.0, min(100.0, float(raw))), 2)
            except (TypeError, ValueError):
                return round(default, 2)

        keywords = [str(item).strip() for item in payload.get("keywords", []) if str(item).strip()][:8]
        topics = [str(item).strip() for item in payload.get("topics", []) if str(item).strip()]
        entities = [str(item).strip() for item in payload.get("entities", []) if str(item).strip()]
        tags = [str(item).strip().lstrip("#") for item in payload.get("tags", []) if str(item).strip()]

        for candidate in fallback.tags:
            if candidate not in tags:
                tags.append(candidate)
            if len(tags) == 2:
                break

        while len(tags) < 2:
            tags.append(fallback.tags[len(tags)])

        market_bias = str(payload.get("market_bias", fallback.market_bias)).strip().lower()
        if market_bias not in {"bullish", "bearish", "neutral"}:
            market_bias = fallback.market_bias

        return AnalysisResult(
            sentiment_score=clamp_sentiment(fallback.sentiment_score),
            fear_greed_score=clamp_score("fear_greed_score", fallback.fear_greed_score),
            hate_score=clamp_score("hate_score", fallback.hate_score),
            hate_index=clamp_score("hate_index", fallback.hate_index),
            uncertainty_score=clamp_score("uncertainty_score", fallback.uncertainty_score),
            market_bias=market_bias,
            keywords=keywords or fallback.keywords,
            tags=tags[:2],
            topics=topics or fallback.topics,
            entities=entities or fallback.entities,
        )
