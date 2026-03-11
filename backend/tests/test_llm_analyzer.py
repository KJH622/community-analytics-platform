from app.analytics.llm_analyzer import LLMCommunityAnalyzer


def test_llm_analyzer_normalizes_payload_with_fallback_tags():
    analyzer = LLMCommunityAnalyzer()
    result = analyzer._normalize_payload(
        {
            "sentiment_score": -12,
            "fear_greed_score": 22,
            "hate_score": 61,
            "hate_index": 58,
            "uncertainty_score": 44,
            "market_bias": "bearish",
            "keywords": ["전쟁", "유가"],
            "tags": ["전쟁리스크"],
            "topics": ["geopolitics"],
            "entities": ["이란"],
        },
        title="호르무즈 포격",
        body="전쟁 리스크로 유가가 오른다",
    )

    assert result.market_bias == "bearish"
    assert result.hate_score == 61
    assert len(result.tags) == 2
    assert result.tags[0] == "전쟁리스크"


def test_llm_analyzer_falls_back_to_rule_based_without_client():
    analyzer = LLMCommunityAnalyzer()
    analyzer.client = None

    result = analyzer.analyze("진짜 역겹다", "커뮤니티가 쓰레기 됐다")

    assert result.hate_score > 0
