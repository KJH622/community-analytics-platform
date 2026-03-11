from app.analytics.rule_based import RuleBasedAnalyzer
from app.politics.analytics.rule_based import PoliticalRuleBasedAnalyzer


def test_market_rule_based_sentiment_positive():
    analyzer = RuleBasedAnalyzer()
    result = analyzer.analyze(
        "엔비디아 반등 rally",
        "반도체 호재와 AI 수요 덕분에 주가 상승 기대가 커진다",
    )
    assert result.sentiment_score > 0
    assert result.market_bias in {"bullish", "neutral"}


def test_market_rule_based_returns_two_tags_and_percentage_scores():
    analyzer = RuleBasedAnalyzer()
    result = analyzer.analyze(
        "패닉셀 와중에 금리 결정도 불확실",
        "공포와 불안이 너무 크고 증오 섞인 표현까지 나오면서 시장 방향이 애매하다",
    )
    assert 0 <= result.hate_score <= 100
    assert 0 <= result.uncertainty_score <= 100
    assert 0 <= result.fear_greed_score <= 100
    assert 0 <= result.hate_index <= 100
    assert len(result.tags) == 2


def test_market_rule_based_detects_colloquial_korean_expressions():
    analyzer = RuleBasedAnalyzer()
    result = analyzer.analyze(
        "진짜 역겹다 다 망해라",
        "이딴 글 쓰는 애들 때문에 커뮤니티가 쓰레기 됐다",
    )
    assert result.hate_score > 50
    assert result.hate_index > 40
    assert "커뮤니티반응" in result.tags


def test_political_rule_based_labels():
    analyzer = PoliticalRuleBasedAnalyzer()
    result = analyzer.analyze(
        "후보 지지층 결집",
        "후보 지지층이 빠르게 모이며 반응도 강해졌다",
        ["정치", "선거"],
    )
    assert "지지" in result.labels
    assert result.election_heat_index > 0
