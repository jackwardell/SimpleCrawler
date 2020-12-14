import pytest

from crawler.parser import get_links_from_html


def make_html(body: str) -> str:
    return f"<html><head></head><body>{body}</body></html>"


def make_a_tag(path: str) -> str:
    return f'<a href="{path}">{path}</a>'


def make_a_tags(paths: list) -> str:
    return "<br>".join([make_a_tag(path) for path in paths])


ABSOLUTE_LINK = ["https://example.com"]
RELATIVE_LINK = ["/example.html"]
GET_ARGS_LINK = ["/example?hello=world&world=hello"]
FRAGMENT_LINK = ["#hello"]
MULTIPLE_LINKS = ABSOLUTE_LINK + RELATIVE_LINK + GET_ARGS_LINK + FRAGMENT_LINK

LINK_EXAMPLES = [
    ABSOLUTE_LINK,
    RELATIVE_LINK,
    GET_ARGS_LINK,
    FRAGMENT_LINK,
    MULTIPLE_LINKS,
]

HTML_SNIPPETS_AND_RESULT = [
    (make_html(make_a_tags(example)), set(example)) for example in LINK_EXAMPLES
]


@pytest.mark.parametrize("html_and_result", HTML_SNIPPETS_AND_RESULT)
def test_parser(html_and_result):
    html, result = html_and_result
    assert get_links_from_html(html) == result
