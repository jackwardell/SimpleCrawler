import pytest
from click.testing import CliRunner

from simple_crawler.cli import crawl
from simple_crawler.cli import DEFAULT_CHECK_HEAD
from simple_crawler.cli import DEFAULT_DISOBEY_ROBOTS
from simple_crawler.cli import DEFAULT_MAX_WORKERS
from simple_crawler.cli import DEFAULT_TIMEOUT
from simple_crawler.cli import DEFAULT_WITH_FRAGMENT
from simple_crawler.cli import DEFAULT_WITH_QUERY
from simple_crawler.crawler import DEFAULT_USER_AGENT
from tests.conftest import make_html_from_links


@pytest.fixture(scope="module")
def runner():
    return CliRunner()


def test_crawl_default(runner):
    test_url = "https://www.example.com"
    result = runner.invoke(crawl, [test_url, "--debug"])
    assert result.output == (
        f"crawling URL: {test_url}\n"
        f"debug mode is on: crawling not running\n"
        f"user agent: {DEFAULT_USER_AGENT}\n"
        f"max workers: {DEFAULT_MAX_WORKERS}\n"
        f"timeout: {DEFAULT_TIMEOUT}\n"
        f"obey robots: {not DEFAULT_DISOBEY_ROBOTS}\n"
        f"check head: {DEFAULT_CHECK_HEAD}\n"
        f"trim query: {not DEFAULT_WITH_QUERY}\n"
        f"trim fragment: {not DEFAULT_WITH_FRAGMENT}\n"
    )


@pytest.mark.parametrize("url", ["https://www.example.com", "http://localhost:5000"])
@pytest.mark.parametrize("user_agent", [["-u", "Test"], ["--user-agent", "tester"]])
@pytest.mark.parametrize("max_workers", [["-w", "10"], ["--max-workers", "10"]])
@pytest.mark.parametrize("timeout", [["-t", "30"], ["--timeout", "30"]])
@pytest.mark.parametrize("check_head", ["-h", "--check-head"])
@pytest.mark.parametrize("disobey_robots", ["-d", "--disobey-robots"])
@pytest.mark.parametrize("with_query", ["-wq", "--with-query"])
@pytest.mark.parametrize("with_fragment", ["-wf", "--with-fragment"])
def test_crawl_options_debug(
    runner,
    url,
    user_agent,
    max_workers,
    timeout,
    check_head,
    disobey_robots,
    with_query,
    with_fragment,
):
    params = (
        [url, check_head, disobey_robots, with_query, with_fragment, "--debug"]
        + user_agent
        + max_workers
        + timeout
    )

    result = runner.invoke(crawl, params)
    assert result.exit_code == 0

    assert result.output == (
        f"crawling URL: {url}\n"
        f"debug mode is on: crawling not running\n"
        f"user agent: {user_agent[1] if user_agent[0] else DEFAULT_USER_AGENT}\n"
        f"max workers: {max_workers[1] if max_workers[0] else DEFAULT_MAX_WORKERS}\n"
        f"timeout: {timeout[1] if timeout[0] else DEFAULT_TIMEOUT}\n"
        f"obey robots: {not bool(disobey_robots)}\n"
        f"check head: {bool(check_head)}\n"
        f"trim query: {not bool(with_query)}\n"
        f"trim fragment: {not bool(with_fragment)}\n"
    )


def test_crawl(server, runner):
    @server.app.route("/")
    def index():
        return make_html_from_links(["/", "/hello", "/world", "/hello/world"])

    @server.app.route("/hello")
    def hello():
        return make_html_from_links(["/", "/hello", "/world", "/hello/world"])

    @server.app.route("/world")
    def world():
        return make_html_from_links(["/", "/hello", "/world", "/hello/world"])

    @server.app.route("/hello/world")
    def hello_world():
        return make_html_from_links(["/", "/hello", "/world", "/hello/world"])

    with server.run():
        result = runner.invoke(crawl, [server.url])
        assert result.exit_code == 0
        assert result.output.startswith("crawling URL: http://0.0.0.0:9999\n")
        assert "crawling http://0.0.0.0:9999/\n" in result.output
        assert "crawling http://0.0.0.0:9999/world\n" in result.output
        assert "crawling http://0.0.0.0:9999/hello/world\n" in result.output
        assert "crawling http://0.0.0.0:9999/hello\n" in result.output
