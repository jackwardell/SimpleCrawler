import pytest

from web_crawler.hyperlink import make_hyperlink
from web_crawler.hyperlink import make_hyperlink_collection


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
def test_hyperlink(input_link_and_output_result):
    input_link, output_result = input_link_and_output_result
    href = make_hyperlink(input_link)
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
    href = make_hyperlink(input_link)
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
    href = make_hyperlink(input_link)
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
    href = make_hyperlink(input_link)
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
        ("?hello=world+hello world", "/?hello=world%2Bhello+world"),
        (
            "/hello-world?hello=world+hello+world",
            "/hello-world?hello=world%2Bhello%2Bworld",
        ),
        ("/?world=hello&hello=world", "/?hello=world&world=hello"),
    ],
)
def test_hyperlink_normalisation(input_link_and_output_result):
    input_link, output_result = input_link_and_output_result
    assert make_hyperlink(input_link).url == output_result


def test_hyperlink_collection_behaves_like_list():
    hrefs = [
        make_hyperlink("/hello"),
        make_hyperlink("/world"),
        make_hyperlink("/?hello=world"),
    ]
    # check __init__
    links = make_hyperlink_collection(hrefs)
    # check __len__
    assert len(links) == 3
    # check append
    links.append(make_hyperlink("/?hello=world&world=hello"))
    # check __len__ again
    assert len(links) == 4
    # check __getitem__
    assert links[0] == make_hyperlink("/hello")
    assert links[3] == make_hyperlink("/?hello=world&world=hello")
    # check __contains__
    for href in hrefs:
        assert href in links
    # check __iter__
    for index, link in enumerate(links):
        assert hrefs[index] == link


@pytest.mark.parametrize(
    "input_and_output_links",
    [
        (["/"], ["/"]),
        (["/", "/"], ["/"]),
        (["/hello", "/hello", "/hello", "/world"], ["/hello", "/world"]),
    ],
)
def test_hyperlink_collection_dedupe(input_and_output_links):
    input_links, output_links = input_and_output_links
    links = make_hyperlink_collection([make_hyperlink(link) for link in input_links])
    assert links.dedupe() == make_hyperlink_collection(
        [make_hyperlink(link) for link in output_links]
    )


@pytest.mark.parametrize(
    "input_and_output",
    [
        (["/", "/"], ["/", "/"]),
        (["hello", "world"], ["/hello", "/world"]),
        (["www.example.com"], ["/www.example.com"]),
    ],
)
def test_hyperlink_collection_relative_links_join_all(input_and_output):
    input_links, output_links = input_and_output
    links = make_hyperlink_collection([make_hyperlink(link) for link in input_links])
    domain = "https://www.google.com"
    assert links.join_all(domain).collection == [
        make_hyperlink(domain + link) for link in output_links
    ]


@pytest.mark.parametrize(
    "input_and_output",
    [
        (["https://www.google.com/"], ["https://www.google.com/"]),
        (
            ["https://hello.world", "https://world.hello"],
            ["https://hello.world", "https://world.hello"],
        ),
        (["http://www.example.com"], ["http://www.example.com"]),
    ],
)
def test_hyperlink_collection_absolute_links_join_all(input_and_output):
    input_links, output_links = input_and_output
    links = make_hyperlink_collection([make_hyperlink(link) for link in input_links])
    domain = "https://www.google.com"
    assert links.join_all(domain).collection == [make_hyperlink(link) for link in output_links]


@pytest.mark.parametrize(
    "fields_and_input_links_and_output_links",
    [
        (
            ("scheme", "http"),
            [
                "http://www.google.com/",
                "/hello-world?hello=world",
                "#hello",
                "/?hello=world#hello",
                "https://www.example.com",
                "https://example.com/hello-world?world=hello",
            ],
            ["http://www.google.com/"],
        ),
        (
            ("authority", ":@www.EXAMPLE.com."),
            [
                "/",
                "/hello-world?hello=world",
                "#hello",
                "/?hello=world#hello",
                "https://www.example.com",
                "https://www.example.com/hello-world?world=hello",
            ],
            [
                "https://www.example.com",
                "https://www.example.com/hello-world?world=hello",
            ],
        ),
        (
            ("path", "/hello-world"),
            [
                "/",
                "/hello-world?hello=world",
                "#hello",
                "/?hello=world#hello",
                "https://www.example.com",
                "https://example.com/hello-world?world=hello",
            ],
            [
                "/hello-world?hello=world",
                "https://example.com/hello-world?world=hello",
            ],
        ),
        (
            ("query", "hello=world"),
            [
                "/",
                "/hello-world?hello=world",
                "#hello",
                "/?hello=world#hello",
                "https://www.example.com",
                "https://example.com/?world=hello",
            ],
            [
                "/hello-world?hello=world",
                "/?hello=world#hello",
            ],
        ),
        (
            ("fragment", "hello"),
            [
                "/",
                "/hello-world?hello=world",
                "#goodbye",
                "/?hello=world#hello",
                "https://www.example.com",
                "https://example.com/#hello",
            ],
            ["/?hello=world#hello", "https://example.com/#hello"],
        ),
    ],
)
def test_hyperlink_collection_filter_by(
    fields_and_input_links_and_output_links,
):
    fields, input_links, output_links = fields_and_input_links_and_output_links

    input_hrefs = make_hyperlink_collection([make_hyperlink(link) for link in input_links])
    k, v = fields
    filtered_hrefs = input_hrefs.filter_by(**{k: v})

    output_hrefs = make_hyperlink_collection([make_hyperlink(link) for link in output_links])

    assert filtered_hrefs == output_hrefs


@pytest.mark.parametrize(
    "fields_and_input_links_and_output_links",
    [
        (
            {"scheme": "http", "authority": "www.example.com"},
            [
                "http://www.google.com./",
                "/hello-world?hello=world",
                "#hello",
                "/?hello=world#hello",
                "http://www.example.com",
                "https://example.com/hello-world?world=hello",
            ],
            ["http://www.example.com"],
        ),
        (
            {
                "authority": "www.example.com",
                "path": "/hello-world",
                "query": "world=hello",
            },
            [
                "/",
                "/hello-world?hello=world",
                "#hello",
                "/?hello=world#hello",
                "https://www.example.com",
                "https://www.example.com/hello-world?world=hello",
            ],
            ["https://www.example.com/hello-world?world=hello"],
        ),
        (
            {"path": "/hello", "query": "hello=world", "fragment": "here"},
            [
                "/hello?hello=world#here",
                "/hello-world?hello=world",
                "#hello",
                "/?hello=world#hello",
                "https://www.example.com",
                "https://yoyoyo.co.uk/hello?hello=world#here",
            ],
            [
                "/hello?hello=world#here",
                "https://yoyoyo.co.uk/hello?hello=world#here",
            ],
        ),
        (
            {
                "scheme": "https",
                "authority": "www.example.com",
                "path": "/",
                "query": "",
                "fragment": "",
            },
            [
                "/",
                "/hello-world?hello=world",
                "#hello",
                "/?hello=world#hello",
                "https://www.example.com",
                "https://example.com/?world=hello",
            ],
            ["https://www.example.com"],
        ),
        (
            {
                "scheme": "HTTPS",
                "authority": "@www.example.com",
                "path": "/",
                "query": "",
                "fragment": "",
            },
            [
                "/",
                "/hello-world?hello=world",
                "#hello",
                "/?hello=world#hello",
                "https://www.yoyoyo.com",
                "https://example.com/?world=hello",
            ],
            [],
        ),
    ],
)
def test_hyperlink_collection_filter_by_mutli_kwargs(
    fields_and_input_links_and_output_links,
):
    fields, input_links, output_links = fields_and_input_links_and_output_links

    input_hrefs = make_hyperlink_collection([make_hyperlink(link) for link in input_links])
    filtered_hrefs = input_hrefs.filter_by(**fields)

    output_hrefs = make_hyperlink_collection([make_hyperlink(link) for link in output_links])

    assert filtered_hrefs == output_hrefs
