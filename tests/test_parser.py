import pytest

from crawler.parser import AnchorTagParser
from crawler.parser import get_hrefs_from_html
from crawler.parser import HyperlinkReference
from crawler.parser import HyperlinkReferenceCollection


def make_html(body: str) -> str:
    """make a html doc by passing data to appear in <body> tag"""
    return f"<html><head></head><body>{body}</body></html>"


def make_a_tag(path: str) -> str:
    """make a <a> tag with path as HREF value"""
    return f'<a href="{path}">another link</a>'


def make_a_tags(paths: list) -> str:
    """make multiple <a> tags (via `make_a_tag`) seperated by <br> tags"""
    return "<br>".join([make_a_tag(path) for path in paths])


@pytest.mark.parametrize(
    "input_link_and_output_result",
    [
        ("/", "/"),
        (".", "/"),
        ("example", "/example"),
        ("/example", "/example"),
        ("www.example.html", "/www.example.html"),
        ("#hello", "/#hello"),
        ("/#hello", "/#hello"),
        ("example#hello", "/example#hello"),
        ("/example#hello", "/example#hello"),
        ("?hello=world", "/?hello=world"),
        ("/?hello=world", "/?hello=world"),
        ("https://www.example.com/", "https://www.example.com/"),
        ("https://www.example.com.", "https://www.example.com/"),
        ("https://www.example.com/example", "https://www.example.com/example"),
        ("https://www.example.com#hello", "https://www.example.com/#hello"),
        ("https://www.example.com/#hello", "https://www.example.com/#hello"),
        (
            "https://www.example.com/example#hello",
            "https://www.example.com/example#hello",
        ),
        ("https://www.example.com?hello=world", "https://www.example.com/?hello=world"),
        (
            "https://www.example.com/?hello=world",
            "https://www.example.com/?hello=world",
        ),
    ],
)
def test_hyperlink_reference(input_link_and_output_result):
    input_link, output_result = input_link_and_output_result
    href = HyperlinkReference(input_link)
    assert str(href) == output_result


@pytest.mark.parametrize(
    "input_link_and_output_result",
    [
        ("/", False),
        (".", False),
        ("example", False),
        ("/example", False),
        ("www.example.html", False),
        ("#hello", False),
        ("/#hello", False),
        ("example#hello", False),
        ("/example#hello", False),
        ("?hello=world", False),
        ("/?hello=world", False),
        ("https://www.example.com/", True),
        ("https://www.example.com.", True),
        ("https://www.example.com/example", True),
        ("https://www.example.com#hello", True),
        ("https://www.example.com/#hello", True),
        ("https://www.example.com/example#hello", True),
        ("https://www.example.com?hello=world", True),
        ("https://www.example.com/?hello=world", True),
    ],
)
def test_hyperlink_is_absolute_or_relative(input_link_and_output_result):
    input_link, output_result = input_link_and_output_result
    href = HyperlinkReference(input_link)
    assert href.is_absolute is output_result
    assert href.is_relative is not output_result


@pytest.mark.parametrize(
    "input_link_and_output_result",
    [
        ("/", "/"),
        (".", "/"),
        ("example", "/example"),
        ("/example", "/example"),
        ("www.example.html", "/www.example.html"),
        ("#hello", "/#hello"),
        ("/#hello", "/#hello"),
        ("example#hello", "/example#hello"),
        ("/example#hello", "/example#hello"),
        ("?hello=world", "/?hello=world"),
        ("/?hello=world", "/?hello=world"),
    ],
)
def test_hyperlink_join_with_relative_links(input_link_and_output_result):
    input_link, output_result = input_link_and_output_result
    href = HyperlinkReference(input_link)
    domain = "https://helloworld.com"
    assert str(href.join(domain)) == domain + output_result


@pytest.mark.parametrize(
    "input_link_and_output_result",
    [
        ("https://www.example.com/", "https://www.example.com/"),
        ("https://www.example.com.", "https://www.example.com/"),
        ("https://www.example.com/example", "https://www.example.com/example"),
        ("https://www.example.com#hello", "https://www.example.com/#hello"),
        ("https://www.example.com/#hello", "https://www.example.com/#hello"),
        (
            "https://www.example.com/example#hello",
            "https://www.example.com/example#hello",
        ),
        ("https://www.example.com?hello=world", "https://www.example.com/?hello=world"),
        (
            "https://www.example.com/?hello=world",
            "https://www.example.com/?hello=world",
        ),
    ],
)
def test_hyperlink_join_with_absolute_links(input_link_and_output_result):
    input_link, output_result = input_link_and_output_result
    href = HyperlinkReference(input_link)
    domain = "https://helloworld.com"
    assert str(href.join(domain)) == output_result


@pytest.mark.parametrize(
    "input_link_and_output_result",
    [
        ("/ hello world", "/%20hello%20world"),
        ("/example!@£$%^&*()", "/example%21%40%C2%A3%24%%5E%26%2A%28%29"),
        ("www.EXAMPLE.html", "/www.EXAMPLE.html"),
        ("#hello", "/#hello"),
        ("/#hello", "/#hello"),
        ("HTTPS://WWW.eXaMpLe.cOm/", "https://www.example.com/"),
        ("?hello=world+hello+world", "/?hello=world%2Bhello%2Bworld"),
        (
            "/hello-world?hello=world+hello+world",
            "/hello-world?hello=world%2Bhello%2Bworld",
        ),
        ("/?hello=world&world=hello", "/?hello=world&world=hello"),
    ],
)
def test_hyperlink_normalisation(input_link_and_output_result):
    input_link, output_result = input_link_and_output_result
    assert str(HyperlinkReference(input_link)) == output_result


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
    html, href = make_html(make_a_tag(link)), HyperlinkReference(link)
    parser = AnchorTagParser()
    parser.feed(html)
    assert parser.found_links.collection == [href]


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
        [HyperlinkReference(link) for link in links],
    )
    parser = AnchorTagParser()
    parser.feed(html)
    assert parser.found_links.collection == hrefs


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
        [HyperlinkReference(link) for link in links],
    )
    parser = AnchorTagParser()
    parser.feed(html)
    assert parser.found_links.collection == hrefs


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
def test_get_hrefs_from_html_not_unique(links):
    html, hrefs = (
        make_html(make_a_tags(links)),
        [HyperlinkReference(link) for link in links],
    )
    assert get_hrefs_from_html(html).collection == hrefs
    assert get_hrefs_from_html(html, unique=False).collection == hrefs


@pytest.mark.parametrize(
    "input_links_output_results",
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
def test_get_hrefs_from_html_unique(input_links_output_results):
    input_links, output_results = input_links_output_results
    html = make_html(make_a_tags(input_links))
    hrefs = [HyperlinkReference(link) for link in output_results]
    assert get_hrefs_from_html(html, unique=True).collection == hrefs


def test_hyperlink_reference_collection_behaves_like_list():
    hrefs = [
        HyperlinkReference("/hello"),
        HyperlinkReference("/world"),
        HyperlinkReference("/?hello=world"),
    ]
    # check __init__
    links = HyperlinkReferenceCollection(hrefs)
    # check __len__
    assert len(links) == 3
    # check append
    links.append(HyperlinkReference("/?hello=world&world=hello"))
    # check __len__ again
    assert len(links) == 4
    # check __getitem__
    assert links[0] == HyperlinkReference("/hello")
    assert links[3] == HyperlinkReference("/?hello=world&world=hello")
    # check __contains__
    for href in hrefs:
        assert href in links
    # check __iter__
    for index, link in enumerate(links):
        assert hrefs[index] == link
