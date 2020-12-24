import click

from web_crawler.crawler import Crawler
from web_crawler.crawler import DEFAULT_CHECK_HEAD
from web_crawler.crawler import DEFAULT_MAX_WORKERS
from web_crawler.crawler import DEFAULT_OBEY_ROBOTS
from web_crawler.crawler import DEFAULT_TIMEOUT
from web_crawler.crawler import DEFAULT_USER_AGENT


@click.command()
@click.argument("url")
@click.option("-u", "--user-agent", default=DEFAULT_USER_AGENT)
@click.option("-w", "--max-workers", default=DEFAULT_MAX_WORKERS)
@click.option("-t", "--timeout", default=DEFAULT_TIMEOUT)
@click.option("-h", "--check-head", is_flag=True, default=DEFAULT_CHECK_HEAD)
@click.option("-o", "--obey-robots", is_flag=True, default=DEFAULT_OBEY_ROBOTS)
@click.option("--debug/--no-debug", default=False)
def crawl(url, user_agent, max_workers, timeout, check_head, obey_robots, debug):
    click.echo(f"Crawling URL: {url}")
    crawler = Crawler(
        user_agent=user_agent,
        max_workers=max_workers,
        timeout=timeout,
        check_head=check_head,
        obey_robots=obey_robots,
    )

    if debug is False:
        crawler.crawl(url)

    else:
        click.echo("Debug mode is on: crawling not running")
        click.echo(f"crawler User-Agent: {crawler.user_agent}")
        click.echo(f"crawler max workers: {crawler.max_workers}")
        click.echo(f"crawler timeout: {crawler.timeout}")
        click.echo(f"crawler check head: {crawler.check_head}")
        click.echo(f"crawler obey robots: {crawler.obey_robots}")


if __name__ == "__main__":
    crawl()
