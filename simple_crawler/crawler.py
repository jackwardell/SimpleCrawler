"""
module for core software for crawling
"""
import queue
import time
from concurrent.futures import Executor
from concurrent.futures import ThreadPoolExecutor
from typing import Set
from typing import Union
from urllib.robotparser import RobotFileParser

from requests import Session

from simple_crawler.hyperlink import Hyperlink
from simple_crawler.hyperlink import HyperlinkSet
from simple_crawler.hyperlink import make_hyperlink
from simple_crawler.hyperlink import make_hyperlink_set
from simple_crawler.parser import get_hrefs_from_html
from simple_crawler.requester import ClientError
from simple_crawler.requester import Requester
from simple_crawler.requester import ServerError
from simple_crawler.requester import WrongMIMEType

DEFAULT_USER_AGENT = "PySimpleCrawler"


class NoThreadExecutor(Executor):
    """an executor that won't fire off any threads (used for when workers=1)"""

    def submit(self, fn, *args, **kwargs):
        return fn(*args, **kwargs)


class Crawler:
    """
    This the core component for crawling

    How to use?
        * crawler = Crawler(**some_config)
        * found_urls = crawler.crawl(some_url)

    It's that simple

    :param user_agent: (str) name of the user agent, defaults to PyWebCrawler
    :param session: (requests.Session) option to add a requests.Session, useful
                    if you need to add headers
    :param max_workers: (int) number of threads to spin up, when default as 1,
                        there is NO threading
    :param timeout: (int) length of time to wait for another url to be sent to
                    the queue before timing out and shutting down
    :param obey_robots: (bool) should crawler obey robots.txt
    :param check_head: (bool) should crawler check HEAD before GET, useful if
                       there are lots of endpoints with large responses that
                       don't need to be crawled e.g. pdf, .png, etc
    :param trim_query: (bool) should crawler remove ?query=strings from url
    :param trim_fragment: (bool) should crawler remove #fragments from url
    """

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
        self._requester = Requester(user_agent=self.user_agent, session=session)
        self._queue = queue.Queue()
        self._seen_urls = make_hyperlink_set()
        self._done_urls = make_hyperlink_set()

        # todo elements: could allow recording of redirects, client errors & server errors
        self.record_redirects = False
        # self.record_client_errors = False
        # self.record_server_errors = False

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

    def _executor(self) -> Union[ThreadPoolExecutor, NoThreadExecutor]:
        """executor for multi-threaded execution or same script execution if workers=1"""
        executor = (
            ThreadPoolExecutor(max_workers=self.max_workers)
            if self.max_workers != 1
            else NoThreadExecutor()
        )
        return executor

    def _get_hrefs(self, url: Hyperlink) -> HyperlinkSet:
        """get hrefs from url with requester"""
        resp = self._requester(
            url,
            check_head_first=self.check_head,
            follow_redirects=(not self.record_redirects),
        )

        # if we want to record redirects
        # and the response returns a redirect
        # then we will grab the the "Location" header from the response
        # because there will be no links to scrape from the text
        if self.record_redirects and str(resp.status_code).startswith("3"):
            hrefs = make_hyperlink_set([make_hyperlink(resp.headers["Location"])])
        # else we scrape from the text
        else:
            hrefs = get_hrefs_from_html(resp.text)

        return hrefs

    def _parse_hrefs(self, hrefs: HyperlinkSet, url: Hyperlink) -> HyperlinkSet:
        """parse the hrefs from collection and by trimming, joining, filtering and deduping"""
        hrefs = (
            # remove the query part and the fragment part
            hrefs.trim(query=self.trim_query, fragment=self.trim_fragment)
            # join all relative urls to the base url
            .join_all(url)
            # then find all urls that match the base url
            .filter_by(authority=url.authority)
        )

        return hrefs

    def _crawl_url(self, url: Hyperlink) -> None:
        """crawl any url for all the other urls (in <a hrefs=url> tags)"""
        print(f"CRAWLING: {url}")
        # try get 200 responses
        try:
            # get all links on page
            hrefs = self._get_hrefs(url)
            print(f"VISITED: {url}")
            # go through all the links found and print them to console
            for href in hrefs:
                print(f"FOUND: {href} ON {url}")

            # get all unique links from page that match the domain
            hrefs = self._parse_hrefs(hrefs, url)
            # go through all links and add to queue and seen_urls if not in seen_urls
            for href in hrefs:
                if href not in self._seen_urls:
                    self._queue.put(href)
                    self._seen_urls.add(href)

            # set url as done
            self._done_urls.add(url)

        # except 4xx or 5xx
        except (ClientError, ServerError) as exc:
            # NB: we don't set as done here as we don't record responses that
            #     returned 4xx or 5xx status codes
            # todo: as this does not add to done_urls, we will have to wait
            #  for timeout
            print(f"ERROR: {exc} ON {url}")

        # or wrong mime type
        except WrongMIMEType:
            print(f"VISITED: {url}")
            # add to done_urls as it is fair to report .pdf, etc files to found urls
            self._done_urls.add(url)

    def _get_robots(self, domain: Hyperlink) -> RobotFileParser:
        """get the robots.txt from any domain"""
        robots_url = domain.with_path("robots.txt")
        robots = RobotFileParser(str(robots_url))
        # try and get /robots.txt and parse except error we assume none
        try:
            resp = self._requester(robots_url, mime_types=("text/plain",))
            robots.parse(resp.text.splitlines())

        except (ClientError, ServerError, WrongMIMEType):
            robots.parse("")

        return robots

    def crawl(self, domain: str) -> Set[str]:
        """crawl any site for all urls"""
        domain = make_hyperlink(domain)
        self._queue.put(domain)

        # get robots
        # todo: only do this if we obey robots?
        robots = self._get_robots(domain)

        with self._executor() as executor:
            while True:
                # exit if we have crawled all urls found
                if self._seen_urls == self._done_urls and self._seen_urls.is_not_empty():
                    # return results
                    return self._render_results()

                # wait for more urls to enter queue or return if we timeout
                try:
                    url = self._queue.get(timeout=self.timeout)
                except queue.Empty:
                    # return results
                    return self._render_results()

                # if the url has been done start flow again
                if url in self._done_urls:
                    continue

                # if we are to obey the robots then we need to see what we can scrape
                if self.obey_robots:
                    # start again if we can't fetch a url
                    if not robots.can_fetch(self.user_agent, str(url)):
                        print(f"{self.user_agent} can't crawl {url}")
                        continue

                    # there is a bug in py3.6 https://bugs.python.org/issue35922
                    # this try, except will allow for 3.6
                    try:
                        # wait for delay if we can scrape but must crawl slowly
                        if robots.crawl_delay(self.user_agent):
                            delay = int(robots.crawl_delay(self.user_agent))
                            print(f"{self.user_agent} has a delay of {delay}, waiting...")
                            time.sleep(delay)
                    except AttributeError:
                        pass

                # submit crawl_url to executor
                executor.submit(self._crawl_url, url)

    def _render_results(self) -> Set[str]:
        """render all urls as a set of strings and reset crawler"""
        results = {str(url) for url in self._done_urls}
        # reset to start point
        self._queue = queue.Queue()
        self._seen_urls = make_hyperlink_set()
        self._done_urls = make_hyperlink_set()
        return results
