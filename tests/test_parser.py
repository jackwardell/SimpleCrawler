import pytest

from crawler.parser import get_links_from_html

HTML_NO_A_TAGS = "<html><body><h1>hello world</h1></body></html>"
HTML_ONE_A_TAGS = "<html><body><a href='/hello-world'>hello world</a></body></html>"
HTML_TWO_A_TAGS = "<html><body><a href='https://www.google.com'>google</a><a href='/hello-world'>hello world</a></body></html>"

HTML_SNIPPETS_AND_RESULT = [
    (HTML_NO_A_TAGS, set()),
    (HTML_ONE_A_TAGS, {"/hello-world"}),
    (HTML_TWO_A_TAGS, {"https://www.google.com", "/hello-world"}),
]


@pytest.mark.parametrize("html_and_result", HTML_SNIPPETS_AND_RESULT)
def test_parser(html_and_result):
    html, result = html_and_result
    assert get_links_from_html(html) == result
