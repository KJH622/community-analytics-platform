from app.services.text_cleaner import canonicalize_url, clean_text


def test_clean_text_removes_html_and_urls():
    cleaned = clean_text("<p>Hello <b>world</b> https://example.com</p>")
    assert cleaned == "Hello world"


def test_canonicalize_url_strips_query_params():
    assert canonicalize_url("https://example.com/path?a=1") == "https://example.com/path"
