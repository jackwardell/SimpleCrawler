import queue
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.robotparser import RobotFileParser

from requests import Session

from web_crawler.hyperlink import Hyperlink
from web_crawler.hyperlink import make_hyperlink
from web_crawler.parser import get_hrefs_from_html
from web_crawler.requester import ClientError
from web_crawler.requester import Requester
from web_crawler.requester import ServerError
from web_crawler.requester import WrongMIMEType

DEFAULT_TIMEOUT = 10
DEFAULT_MAX_WORKERS = 1
DEFAULT_USER_AGENT = "PyWebCrawler"
DEFAULT_OBEY_ROBOTS = True
DEFAULT_CHECK_HEAD = False


class NoThreadExecutor:
    """an executor that won't fire off any threads"""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def submit(self, fn, *args, **kwargs):
        return fn(*args, **kwargs)


class Crawler:
    """simple multi threaded crawler"""

    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        session: Session = None,
        max_workers: int = DEFAULT_MAX_WORKERS,
        timeout: int = DEFAULT_TIMEOUT,
        obey_robots: bool = DEFAULT_OBEY_ROBOTS,
        check_head: bool = DEFAULT_CHECK_HEAD,
    ):
        self.user_agent = user_agent
        self.requester = Requester(user_agent=user_agent, session=session)

        self.queue = queue.Queue()

        self.seen_urls = set()
        self.done_urls = set()

        self.max_workers = max_workers
        self.timeout = timeout

        self.obey_robots = obey_robots
        self.check_head = check_head

    def executor(self):
        """executor for multi-threaded execution or same script execution if workers=1"""
        executor = (
            ThreadPoolExecutor(max_workers=self.max_workers)
            if self.max_workers != 1
            else NoThreadExecutor()
        )
        return executor

    def crawl_url(self, url: Hyperlink):
        """crawl any url for all the other urls (in <a hrefs=url> tags)"""
        print(f"crawling {url}")
        try:
            resp = self.requester(url, check_head_first=self.check_head)
            hrefs = get_hrefs_from_html(resp.text)
            hrefs = (
                hrefs.without_fragments().join_all(url).filter_by(authority=url.authority).dedupe()
            )
            for href in hrefs:
                if href not in self.seen_urls:
                    self.queue.put(href)
                    self.seen_urls.add(href)

        except (ClientError, ServerError) as exc:
            print(f"{exc} on {url}")

        except WrongMIMEType as exc:
            print(f"{exc} on {url}")

        self.done_urls.add(url)

    def get_robots(self, domain: Hyperlink) -> RobotFileParser:
        """get the robots.txt from any domain"""
        robots_url = domain.with_path("/robots.txt")
        robots = RobotFileParser(str(robots_url))
        try:
            resp = self.requester(robots_url, mime_types=("text/plain",))
            robots.parse(resp.text.splitlines())

        except (ClientError, ServerError, WrongMIMEType):
            robots.parse("")

        return robots

    def crawl(self, domain: str):
        """crawl any site for all urls"""
        domain = make_hyperlink(domain)
        self.queue.put(domain)

        robots = self.get_robots(domain)

        with self.executor() as executor:
            while True:
                # exit if we have crawled all urls found
                if self.seen_urls == self.done_urls and self.seen_urls != set():
                    # return results
                    return self.render_results()

                # wait for more urls to enter queue or return if we timeout
                try:
                    url = self.queue.get(timeout=self.timeout)
                except queue.Empty:
                    # return results
                    return self.render_results()

                # if the url has been done start flow again
                if url in self.done_urls:
                    continue

                # if we are to obey the robots then we need to see what we can scrape
                if self.obey_robots:
                    # start again if we can't fetch a url
                    if not robots.can_fetch(self.user_agent, str(url)):
                        continue

                    # wait for delay if we can scrape but must crawl slowly
                    if robots.crawl_delay(self.user_agent):
                        delay = int(robots.crawl_delay(self.user_agent))
                        time.sleep(delay)

                # submit crawl_url to executor
                executor.submit(self.crawl_url, url)

    def render_results(self):
        """render all urls as a set of strings and reset crawler"""
        results = {str(url) for url in self.done_urls}
        self.queue = queue.Queue()
        self.seen_urls = set()
        self.done_urls = set()
        return results
