import pytest

from crawler.parser import AnchorTagParser
from crawler.parser import get_unique_links_from_html


def make_html(body: str) -> str:
    """make a html doc by passing data to appear in <body> tag"""
    return f"<html><head></head><body>{body}</body></html>"


def make_a_tag(path: str) -> str:
    """make a <a> tag with path as HREF value"""
    return f'<a href="{path}">another link</a>'


def make_a_tags(paths: list) -> str:
    """make multiple <a> tags (via `make_a_tag`) seperated by <br> tags"""
    return "<br>".join([make_a_tag(path) for path in paths])


# some test case examples
ABSOLUTE_LINK = ["https://example.com"]
RELATIVE_LINK = ["/example.html"]
GET_ARGS_LINK = ["/example?hello=world&world=hello"]
FRAGMENT_LINK = ["#hello"]
MULTIPLE_LINKS = ABSOLUTE_LINK + RELATIVE_LINK + GET_ARGS_LINK + FRAGMENT_LINK
DUPLICATE_LINKS = ["https://example.com", "https://example.com"]

# all examples for pytest.mark.parameterize
LINK_EXAMPLES = [
    ABSOLUTE_LINK,
    RELATIVE_LINK,
    GET_ARGS_LINK,
    FRAGMENT_LINK,
    MULTIPLE_LINKS,
    DUPLICATE_LINKS,
]

# make tuples of html and expected links to be found via parser
# e.g. ('<html><body><a href="/some-link">some link</a></body></html>', ["/some-link"])
HTML_SNIPPETS_AND_RESULT = [(make_html(make_a_tags(example)), example) for example in LINK_EXAMPLES]


@pytest.mark.parametrize("html_and_expected_links_to_be_found", HTML_SNIPPETS_AND_RESULT)
def test_anchor_tag_parser(html_and_expected_links_to_be_found):
    html, expected_links_to_be_found = html_and_expected_links_to_be_found
    parser = AnchorTagParser()
    parser.feed(html)
    assert parser.found_links == expected_links_to_be_found


@pytest.mark.parametrize("html_and_expected_links_to_be_found", HTML_SNIPPETS_AND_RESULT)
def test_get_unique_links_from_html(html_and_expected_links_to_be_found):
    html, expected_links_to_be_found = html_and_expected_links_to_be_found
    assert get_unique_links_from_html(html) == set(expected_links_to_be_found)
