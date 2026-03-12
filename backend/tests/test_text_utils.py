from app.utils.text import clean_text, tokenize


def test_clean_text_removes_html_and_urls():
    raw = "<p>hello</p> https://example.com world"
    assert clean_text(raw) == "hello world"


def test_tokenize_handles_korean_and_english():
    tokens = tokenize("대선 후보 토론 inflation data")
    assert "대선" in tokens
    assert "후보" in tokens
    assert "inflation" in tokens
