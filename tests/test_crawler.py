import pytest
from flask import abort
from flask import Flask
from flask import redirect
from flask import request

from tests.conftest import make_html_from_links
from tests.conftest import WebServer
from web_crawler.crawler import Crawler
from web_crawler.crawler import NoThreadExecutor
from web_crawler.hyperlink import make_hyperlink
from web_crawler.hyperlink import make_hyperlink_set
from web_crawler.requester import ClientError
from web_crawler.requester import ServerError
from web_crawler.requester import WrongMIMEType


def some_func(*args, **kwargs):
    return f"{args}, {kwargs}"


ARGS = (1, "two", 3.0)
KWARGS = {"hello": "world", "example": True}


def test_no_thread_executor():
    with NoThreadExecutor() as executor:
        assert some_func(*ARGS, **KWARGS) == executor.submit(some_func, *ARGS, **KWARGS)


@pytest.fixture(scope="function")
def crawler():
    crawler = Crawler(timeout=0)
    assert crawler._queue.empty()
    assert crawler._seen_urls == make_hyperlink_set()
    assert crawler._done_urls == make_hyperlink_set()
    return crawler


@pytest.fixture(scope="module")
def crawler_server():
    """simple server to speed up tests that has all functionality required for most tests"""
    app = Flask("crawler_server")
    server = WebServer(app)
    links = {
        server.url + "/",
        server.url + "/hello",
        server.url + "/world",
        server.url + "/mime/text/pdf",
        server.url + "/mime/image/png",
        server.url + "/mime/text/css",
    }
    dont_find_links = {
        "https://subdomain.example.com/",
        "https://www.example.com/",
        server.url + "/hello",
        "/world",
        "/error/400",
        "/error/500",
    }
    all_links = links | dont_find_links

    @server.app.route("/")
    def index():
        return make_html_from_links(all_links)

    @server.app.route("/hello")
    def hello():
        return "<html><body><a href='/world'>world</a></body></html>"

    @server.app.route("/world")
    def world():
        return "<html><body><a href='/hello'>hello</a></body></html>"

    @server.app.route("/user-agent/<agent_name>")
    def user_agent(agent_name):
        return "" if request.headers["User-Agent"] == agent_name else abort(500)

    @server.app.route("/redirect/<location>")
    def redirect_to(location):
        return redirect("/" + location)

    @server.app.route("/error/<int:code>")
    def error(code):
        abort(code)

    @server.app.route("/mime/<group>/<name>")
    def mime_type(group, name):
        return "", 200, {"Content-Type": f"{group}/{name}"}

    with server.run():
        server.links = links
        yield server


@pytest.mark.parametrize("user_agent", ["hello", "world", "TestAgent"])
def test_crawler_user_agent_success(crawler_server, user_agent):
    crawler = Crawler(user_agent=user_agent, timeout=0)
    found_urls = crawler.crawl(crawler_server.url + f"/user-agent/{user_agent}")
    assert found_urls == {crawler_server.url + f"/user-agent/{user_agent}"}

    crawler = Crawler(user_agent=f"Not{user_agent}", timeout=0)
    found_urls = crawler.crawl(crawler_server.url + f"/user-agent/{user_agent}")
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


@pytest.mark.parametrize(
    "record_redirects, found_link", [(False, "/world"), (True, "{host}/hello")]
)
def test_crawler_get_hrefs(crawler_server, crawler, record_redirects, found_link):
    crawler.record_redirects = record_redirects
    found_link = found_link.format(host=crawler_server.url)
    assert crawler._get_hrefs(crawler_server.href + "/redirect/hello") == make_hyperlink_set(
        [found_link]
    )


@pytest.mark.parametrize("code, exc", [("404", ClientError), ("500", ServerError)])
def test_crawler_get_hrefs_fails_error(crawler_server, crawler, code, exc):
    with pytest.raises(exc):
        crawler._get_hrefs(crawler_server.href / "error" / code)


def test_crawler_get_hrefs_fails_mime(crawler_server, crawler):
    with pytest.raises(WrongMIMEType):
        crawler._get_hrefs(crawler_server.href / "mime" / "image" / "png")


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


def test_crawler_crawl_url(crawler_server, crawler):
    crawler._crawl_url(crawler_server.href / "hello")
    assert crawler._queue.get() == crawler_server.href / "world"
    assert crawler._seen_urls == make_hyperlink_set([crawler_server.href / "world"])
    assert crawler._done_urls == make_hyperlink_set([crawler_server.href / "hello"])


def test_crawler_get_robots(crawler_server, crawler):
    user_agent = "Tester"
    allow = ["/this/", "/that/"]
    disallow = ["/hello", "/world"]
    delay = 1

    @crawler_server.app.route("/robots.txt")
    def robots_txt():
        allows = "\n".join([f"Allow: {a}" for a in allow])
        disallows = "\n".join([f"Disallow: {d}" for d in disallow])
        txt = f"""
        User-agent: {user_agent}
        {allows}
        {disallows}
        Crawl-delay: {delay}

        User-agent: NotAnyOtherAgent
        Disallow: /
        """
        return txt, 200, {"Content-Type": "text/plain; charset=utf-8"}

    robots = crawler._get_robots(crawler_server.href / "robots.txt")
    for a in allow:
        assert robots.can_fetch(user_agent, a) is True
    for d in disallow:
        assert robots.can_fetch(user_agent, d) is False
    assert robots.crawl_delay(user_agent) == delay

    assert robots.can_fetch("NotAnyOtherAgent", "/") is False


def test_crawler_crawl_find_all_links(crawler_server, crawler):
    found_links = crawler.crawl(crawler_server.url)
    assert found_links == crawler_server.links


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
