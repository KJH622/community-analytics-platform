from app.analytics.rule_based import RuleBasedAnalyzer
from app.politics.analytics.rule_based import PoliticalRuleBasedAnalyzer


def test_market_rule_based_sentiment_positive():
    analyzer = RuleBasedAnalyzer()
    result = analyzer.analyze("나스닥 반등 기대", "반도체 강세와 랠리 기대가 커졌다")
    assert result.sentiment_score > 0
    assert result.market_bias in {"bullish", "neutral"}


def test_political_rule_based_labels():
    analyzer = PoliticalRuleBasedAnalyzer()
    result = analyzer.analyze(
        "대선 후보 지지층 결집",
        "후보 지지와 열광이 커지고 반대도 강해졌다",
        ["김민준", "이서현"],
    )
    assert "지지" in result.labels
    assert result.election_heat_index > 0
