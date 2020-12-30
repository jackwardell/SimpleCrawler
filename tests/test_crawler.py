import mimetypes

import pytest
from flask import abort
from flask import request

from tests.conftest import make_html_from_links
from web_crawler.crawler import Crawler
from web_crawler.crawler import NoThreadExecutor
from web_crawler.hyperlink import make_hyperlink
from web_crawler.hyperlink import make_hyperlink_set


def some_func(*args, **kwargs):
    return f"{args}, {kwargs}"


ARGS = (1, "two", 3.0)
KWARGS = {"hello": "world", "example": True}


@pytest.fixture(scope="function")
def crawler():
    crawler = Crawler(timeout=0)
    assert crawler._queue.empty()
    assert crawler._seen_urls == make_hyperlink_set()
    assert crawler._done_urls == make_hyperlink_set()
    return crawler


def test_no_thread_executor():
    with NoThreadExecutor() as executor:
        assert some_func(*ARGS, **KWARGS) == executor.submit(some_func, *ARGS, **KWARGS)


def test_crawler_simple_crawl(server, crawler):
    @server.app.route("/hello")
    def hello():
        return "<html><body><a href='/world'>world</a></body></html>"

    @server.app.route("/world")
    def world():
        return "<html><body><a href='/hello'>hello</a></body></html>"

    with server.run():
        found_urls = crawler.crawl(server.url + "/hello")
        assert found_urls == {server.url + "/hello", server.url + "/world"}


def test_crawler_user_agent_success(server):
    user_agent = "TestAgent"

    @server.app.route("/")
    def index():
        return "" if request.headers["User-Agent"] == user_agent else abort(404)

    with server.run():
        crawler = Crawler(user_agent=user_agent, timeout=0)
        found_urls = crawler.crawl(server.url)
        assert found_urls == {server.url + "/"}

        crawler = Crawler(user_agent=f"Not{user_agent}", timeout=0)
        found_urls = crawler.crawl(server.url)
        assert found_urls == set()


@pytest.mark.parametrize("user_agent", ["hello", "world"])
@pytest.mark.parametrize("max_workers", [1, 100])
@pytest.mark.parametrize("timeout", [0, 60])
@pytest.mark.parametrize("obey_robots", [True, False])
@pytest.mark.parametrize("check_head", [True, False])
@pytest.mark.parametrize("trim_query", [True, False])
@pytest.mark.parametrize("trim_fragment", [True, False])
def test_crawler_config(
    user_agent,
    max_workers,
    timeout,
    obey_robots,
    check_head,
    trim_query,
    trim_fragment,
):
    crawler = Crawler(
        user_agent=user_agent,
        max_workers=max_workers,
        timeout=timeout,
        obey_robots=obey_robots,
        check_head=check_head,
        trim_query=trim_query,
        trim_fragment=trim_fragment,
    )

    assert crawler.config == dict(
        user_agent=user_agent,
        max_workers=max_workers,
        timeout=timeout,
        obey_robots=obey_robots,
        check_head=check_head,
        trim_query=trim_query,
        trim_fragment=trim_fragment,
    )


def test_crawler_executor(crawler):
    with crawler._executor() as e:
        assert some_func(ARGS, KWARGS) == e.submit(some_func, ARGS, KWARGS)


def test_crawler_parse_hrefs(crawler):
    host_link = make_hyperlink("https://www.example.com")
    links = [
        "https://www.example.com#with-fragment",
        "https://www.example.com?with=query",
        "https://www.example.com/?with=query#with-fragment",
        "#with-fragment",
        "?with=query",
        "/?with=query#with-fragment",
        "/some/path",
        "/another/path",
        "https://www.example.com/",
        "https://www.example.com/",
        "https://www.example.com/third/path",
        "https://www.dont-find.com",
        "https://www.subdomain.example.com",
    ]
    input_hrefs = make_hyperlink_set([make_hyperlink(link) for link in links])
    assert crawler._parse_hrefs(input_hrefs, host_link) == make_hyperlink_set(
        [
            host_link,
            host_link + "/some/path",
            host_link + "/another/path",
            host_link + "/third/path",
        ]
    )


def test_crawler_crawl_url(server, crawler):
    @server.app.route("/hello")
    def hello():
        return "<html><body><a href='/world'>world</a></body></html>"

    @server.app.route("/world")
    def world():
        return "<html><body><a href='/hello'>hello</a></body></html>"

    with server.run():
        crawler._crawl_url(server.href / "hello")
        assert crawler._queue.get() == server.href / "world"
        assert crawler._seen_urls == make_hyperlink_set([server.href / "world"])
        assert crawler._done_urls == make_hyperlink_set([server.href / "hello"])


def test_crawler_crawl_url_fails(server, crawler):
    crawler.record_client_errors = True


def test_crawler_crawl_find_all_links(server, crawler):
    links = {"/", "/hello", "/world"}
    server_links = {server.url + link for link in links}

    @server.app.route("/")
    def index():
        return make_html_from_links(links)

    @server.app.route("/hello")
    def hello():
        return make_html_from_links(links)

    @server.app.route("/world")
    def world():
        return make_html_from_links(links)

    with server.run():
        found_links = crawler.crawl(server.url)
        assert found_links == server_links


def test_crawler_crawl_nested_links(server, crawler):
    links = {"/", "/hello", "/world"}
    server_links = {server.url + link for link in links}

    @server.app.route("/")
    def index():
        return make_html_from_links(["/hello"])

    @server.app.route("/hello")
    def hello():
        return make_html_from_links(["/world"])

    @server.app.route("/world")
    def world():
        return make_html_from_links(["/"])

    with server.run():
        found_links = crawler.crawl(server.url)
        assert found_links == server_links


def test_crawler_crawl_find_correct_links(server, crawler):
    links = {
        "https://subdomain.example.com/",
        "https://www.example.com/",
        server.url + "/hello",
        "/world",
        "/error/400",
        "/error/500",
    }

    @server.app.route("/")
    def index():
        return make_html_from_links(links)

    @server.app.route("/hello")
    def hello():
        return make_html_from_links(links)

    @server.app.route("/world")
    def world():
        return make_html_from_links(links)

    @server.app.route("/error/<int:code>")
    def error(code):
        abort(code)

    with server.run():
        found_links = crawler.crawl(server.url)
        assert found_links == {
            server.url + "/",
            server.url + "/hello",
            server.url + "/world",
        }


def test_crawler_crawl_find_mime_types(server, crawler):
    links = {
        "/a.css",
        "/b.jpg",
        "/c.pdf",
        "/d.txt",
    }

    @server.app.route("/")
    def index():
        return make_html_from_links(links)

    @server.app.route("/<file_and_extension>")
    def file(file_and_extension):
        return "", 200, {"Content-Type": mimetypes.guess_type(file_and_extension)[0]}

    with server.run():
        found_links = crawler.crawl(server.url)
        assert found_links == {server.url + link for link in links} | {server.url + "/"}


def test_crawler_render_results(crawler):
    assert crawler._queue.empty()
    assert crawler._seen_urls == make_hyperlink_set()
    assert crawler._done_urls == make_hyperlink_set()

    crawler._queue.put("job")
    crawler._seen_urls = make_hyperlink_set(["/hello", "world"])
    crawler._done_urls = make_hyperlink_set(["/this", "/that"])

    results = crawler._render_results()
    assert results == {"/this", "/that"}
    assert crawler._queue.empty()
    assert crawler._seen_urls == make_hyperlink_set()
    assert crawler._done_urls == make_hyperlink_set()
