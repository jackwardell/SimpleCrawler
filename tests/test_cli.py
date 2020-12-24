import pytest
from click.testing import CliRunner

from web_crawler.cli import crawl
from web_crawler.cli import DEFAULT_CHECK_HEAD
from web_crawler.cli import DEFAULT_TIMEOUT
from web_crawler.cli import DEFAULT_USER_AGENT

TEST_URL = "https://www.example.com"


@pytest.mark.parametrize("user_agent", [("-u", "Tester"), ("--user-agent", "Tester"), None])
@pytest.mark.parametrize("timeout", [("-t", "30"), ("--timeout", "30"), None])
@pytest.mark.parametrize("check_head", ["-h", "--check-head", None])
def test_crawl_debug(user_agent, timeout, check_head):
    runner = CliRunner()

    user_agent_arg = [] if user_agent is None else [user_agent[0], user_agent[1]]
    timeout_arg = [] if timeout is None else [timeout[0], timeout[1]]
    check_head_arg = [] if check_head is None else [check_head]

    params = [TEST_URL] + user_agent_arg + timeout_arg + check_head_arg + ["--debug"]

    result = runner.invoke(crawl, params)
    assert result.exit_code == 0

    assert (
        result.output == f"Crawling URL: {TEST_URL}\n"
        f"Debug mode is on: crawling not running\n"
        f"crawler User-Agent: {user_agent[1] if user_agent else DEFAULT_USER_AGENT}\n"
        f"crawler timeout: {timeout[1] if timeout else DEFAULT_TIMEOUT}\n"
        f"crawler check head: {not DEFAULT_CHECK_HEAD if check_head else DEFAULT_CHECK_HEAD}\n"
    )
