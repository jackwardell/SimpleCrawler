import click

from web_crawler.crawler import Crawler
from web_crawler.crawler import DEFAULT_CHECK_HEAD
from web_crawler.crawler import DEFAULT_TIMEOUT
from web_crawler.crawler import DEFAULT_USER_AGENT


@click.command()
@click.argument("url")
@click.option("-u", "--user-agent", default=DEFAULT_USER_AGENT)
@click.option("-t", "--timeout", default=DEFAULT_TIMEOUT)
@click.option("-h", "--check-head", is_flag=True, default=DEFAULT_CHECK_HEAD)
@click.option("--debug/--no-debug", default=False)
def crawl(url, user_agent, timeout, check_head, debug):
    click.echo(f"Crawling URL: {url}")
    crawler = Crawler(user_agent=user_agent, timeout=timeout, check_head=check_head)

    if debug is False:
        results = crawler.crawl(url)
        click.echo(f"Found: {results}")

    else:
        click.echo("Debug mode is on: crawling not running")
        click.echo(f"crawler User-Agent: {crawler.user_agent}")
        click.echo(f"crawler timeout: {crawler.timeout}")
        click.echo(f"crawler check head: {crawler.check_head}")
