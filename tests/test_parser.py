import pytest

from simple_crawler.hyperlink import make_hyperlink
from simple_crawler.hyperlink import make_hyperlink_set
from simple_crawler.parser import AnchorTagParser
from simple_crawler.parser import get_hrefs_from_html
from tests.conftest import make_a_tag
from tests.conftest import make_a_tags
from tests.conftest import make_html


@pytest.mark.parametrize(
    "link",
    [
        "https://example.com",
        "http://example.com",
        "mailto://example.com",
        "//example.com",
        "/",
        ".",
        "example",
        "example.html",
        "www.example.html",
        "../example.html",
        "#hello",
        "?hello=world",
        ".git",
        "/example",
        "/example.html",
        "/example#hello",
        "?hello=world",
        "/example?hello=world&world=hello",
    ],
)
def test_anchor_tag_parser_single_link(link):
    html, href = make_html(make_a_tag(link)), make_hyperlink(link)
    parser = AnchorTagParser()
    parser.feed(html)
    assert parser.found_links.collection == {href}
    assert parser.found_links == make_hyperlink_set([href])


@pytest.mark.parametrize(
    "links",
    [
        ["https://example.com", "http://example.com"],
        ["http://example.com", "mailto://example.com", "//example.com"],
        ["/", ".", "example", "example.html"],
        ["www.example.html", "../example.html", "#hello", "?hello=world", ".git"],
        [
            "https://example.com",
            "/example",
            "/example.html",
            "/example#hello",
            "?hello=world",
            "/example?hello=world&world=hello",
        ],
    ],
)
def test_anchor_tag_parser_multiple_links_no_duplicates(links):
    html, hrefs = (
        make_html(make_a_tags(links)),
        {make_hyperlink(link) for link in links},
    )
    parser = AnchorTagParser()
    parser.feed(html)
    assert parser.found_links.collection == hrefs
    assert parser.found_links == make_hyperlink_set(hrefs)


@pytest.mark.parametrize(
    "links",
    [
        [
            "https://example.com",
            "http://example.com",
            "/example",
            "?hello=world",
            "/example?hello=world&world=hello",
        ],
        [
            "/hello-world",
            "http://example.com",
            "mailto://example.com",
            "//example.com",
            "/hello-world",
        ],
        [
            "https://example.com",
            "https://example.com",
            "#hello",
            "#hello",
            "?hello=world",
        ],
    ],
)
def test_anchor_tag_parser_multiple_links_with_duplicates(links):
    html, hrefs = (
        make_html(make_a_tags(links)),
        {make_hyperlink(link) for link in links},
    )
    parser = AnchorTagParser()
    parser.feed(html)
    assert parser.found_links.collection == hrefs
    assert parser.found_links == make_hyperlink_set(hrefs)


@pytest.mark.parametrize(
    "input_links, output_results",
    [
        (
            [
                "https://example.com",
                "http://example.com",
                "/example",
                "?hello=world",
                "/example?hello=world&world=hello",
            ],
            [
                "https://example.com",
                "http://example.com",
                "/example",
                "?hello=world",
                "/example?hello=world&world=hello",
            ],
        ),
        (
            [
                "/hello-world",
                "http://example.com",
                "mailto://example.com",
                "//example.com",
                "/hello-world",
            ],
            [
                "/hello-world",
                "http://example.com",
                "mailto://example.com",
                "//example.com",
            ],
        ),
        (
            [
                "https://example.com",
                "https://example.com",
                "https://example.com",
                "#hello",
                "?hello=world",
            ],
            ["https://example.com", "#hello", "?hello=world"],
        ),
    ],
)
def test_get_hrefs_from_html_unique(input_links, output_results):
    html = make_html(make_a_tags(input_links))
    hrefs = {make_hyperlink(link) for link in output_results}
    assert get_hrefs_from_html(html).collection == hrefs
    assert get_hrefs_from_html(html) == make_hyperlink_set(hrefs)
