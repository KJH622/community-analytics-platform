from app.analytics.rule_based import RuleBasedAnalysisEngine
from app.politics.analytics.rule_based import analyze_political_text


def test_market_rule_based_analysis_scores_bullish_text():
    engine = RuleBasedAnalysisEngine()
    result = engine.analyze("엔비디아 떡상 로켓", "AI 수요 강세로 반등 기대")
    assert result.sentiment_score > 0
    assert result.fear_greed_score > 50
    assert result.market_bias == "bullish"


def test_political_analysis_detects_polarization():
    result = analyze_political_text(
        "이재명 지지층 열광, 반대층 분노",
        "대선 후보를 두고 조롱과 비판이 동시에 커진다",
    )
    assert result.political_polarization_index > 0
    assert result.election_heat_index > 0
