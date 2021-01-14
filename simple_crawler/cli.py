"""
cli application for crawler
"""
import click

from simple_crawler.crawler import Crawler
from simple_crawler.crawler import DEFAULT_USER_AGENT

DEFAULT_MAX_WORKERS = 1
DEFAULT_TIMEOUT = 10
DEFAULT_CHECK_HEAD = False
DEFAULT_DISOBEY_ROBOTS = False
DEFAULT_WITH_QUERY = False
DEFAULT_WITH_FRAGMENT = False


@click.command()
@click.argument("url")
@click.option("-u", "--user-agent", default=DEFAULT_USER_AGENT)
@click.option("-w", "--max-workers", default=DEFAULT_MAX_WORKERS)
@click.option("-t", "--timeout", default=DEFAULT_TIMEOUT)
@click.option("-h", "--check-head", is_flag=True, default=DEFAULT_CHECK_HEAD)
@click.option("-d", "--disobey-robots", is_flag=True, default=DEFAULT_DISOBEY_ROBOTS)
@click.option("-wq", "--with-query", is_flag=True, default=DEFAULT_WITH_QUERY)
@click.option("-wf", "--with-fragment", is_flag=True, default=DEFAULT_WITH_FRAGMENT)
@click.option("--debug/--no-debug", default=False)
def crawl(
    url,
    user_agent,
    max_workers,
    timeout,
    check_head,
    disobey_robots,
    with_query,
    with_fragment,
    debug,
):
    click.echo(f"crawling URL: {url}")
    crawler = Crawler(
        user_agent=user_agent,
        max_workers=max_workers,
        timeout=timeout,
        check_head=check_head,
        obey_robots=(not disobey_robots),
        trim_query=(not with_query),
        trim_fragment=(not with_fragment),
    )

    if debug is False:
        found_links = crawler.crawl(url)
        click.echo(f"WHEN CRAWLING: {url} THE CRAWLER FOUND:")
        for link in found_links:
            click.echo(f"FOUND: {link}")

    else:
        click.echo("debug mode is on: crawling not running")
        # if debug we print config to console
        for k, v in crawler.config.items():
            click.echo(f"{k.replace('_', ' ')}: {v}")
