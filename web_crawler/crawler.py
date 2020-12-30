import queue
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.robotparser import RobotFileParser

from requests import Session

from web_crawler.hyperlink import Hyperlink
from web_crawler.hyperlink import make_hyperlink
from web_crawler.hyperlink import make_hyperlink_set
from web_crawler.parser import get_hrefs_from_html
from web_crawler.requester import ClientError
from web_crawler.requester import Requester
from web_crawler.requester import ServerError
from web_crawler.requester import WrongMIMEType

DEFAULT_USER_AGENT = "PyWebCrawler"


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
        max_workers: int = 1,
        timeout: int = 10,
        obey_robots: bool = True,
        check_head: bool = False,
        trim_query: bool = True,
        trim_fragment: bool = True,
    ):
        # config elements
        self.user_agent = user_agent
        self.max_workers = max_workers
        self.timeout = timeout
        self.obey_robots = obey_robots
        self.check_head = check_head
        self.trim_query = trim_query
        self.trim_fragment = trim_fragment

        # setup internal elements
        self._requester = Requester(user_agent=user_agent, session=session)
        self._queue = queue.Queue()
        self._seen_urls = make_hyperlink_set()
        self._done_urls = make_hyperlink_set()

    @property
    def config(self) -> dict:
        rv = {
            "user_agent": self.user_agent,
            "max_workers": self.max_workers,
            "timeout": self.timeout,
            "obey_robots": self.obey_robots,
            "check_head": self.check_head,
            "trim_query": self.trim_query,
            "trim_fragment": self.trim_fragment,
        }
        return rv

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
            resp = self._requester(url, check_head_first=self.check_head)
            hrefs = get_hrefs_from_html(resp.text)
            hrefs = (
                hrefs.trim(query=self.trim_query, fragment=self.trim_fragment)
                .join_all(url)
                .filter_by(authority=url.authority)
            )
            for href in hrefs:
                if href not in self._seen_urls:
                    self._queue.put(href)
                    self._seen_urls.add(href)

            self._done_urls.add(url)

        except (ClientError, ServerError) as exc:
            print(f"{exc} on {url}")

        except WrongMIMEType as exc:
            print(f"{exc} on {url}")
            self._done_urls.add(url)

    def get_robots(self, domain: Hyperlink) -> RobotFileParser:
        """get the robots.txt from any domain"""
        robots_url = domain.with_path("/robots.txt")
        robots = RobotFileParser(str(robots_url))
        try:
            resp = self._requester(robots_url, mime_types=("text/plain",))
            robots.parse(resp.text.splitlines())

        except (ClientError, ServerError, WrongMIMEType):
            robots.parse("")

        return robots

    def crawl(self, domain: str):
        """crawl any site for all urls"""
        domain = make_hyperlink(domain)
        self._queue.put(domain)

        robots = self.get_robots(domain)

        with self.executor() as executor:
            while True:
                # exit if we have crawled all urls found
                if self._seen_urls == self._done_urls and self._seen_urls.is_not_empty():
                    # return results
                    return self.render_results()

                # wait for more urls to enter queue or return if we timeout
                try:
                    url = self._queue.get(timeout=self.timeout)
                except queue.Empty:
                    # return results
                    return self.render_results()

                # if the url has been done start flow again
                if url in self._done_urls:
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
        results = {str(url) for url in self._done_urls}
        self._queue = queue.Queue()
        self._seen_urls = make_hyperlink_set()
        self._done_urls = make_hyperlink_set()
        return results
