import pytest

from crawler.parser import get_links_from_html

HTML_NO_A_TAGS = "<html><body><h1>hello world</h1></body></html>"

HTML_SNIPPETS_AND_RESULT = [
    (HTML_NO_A_TAGS, set()),
]


@pytest.mark.parametrize("html_and_result", HTML_SNIPPETS_AND_RESULT)
def test_parser(html_and_result):
    html, result = html_and_result
    assert get_links_from_html(html) == result
