import queue

from requests import Session

from web_crawler.hyperlink import Hyperlink
from web_crawler.hyperlink import make_hyperlink
from web_crawler.parser import get_hrefs_from_html
from web_crawler.requester import ClientError
from web_crawler.requester import Requester
from web_crawler.requester import ServerError
from web_crawler.requester import WrongMIMEType

DEFAULT_TIMEOUT = 10
DEFAULT_USER_AGENT = "PyWebCrawler"
DEFAULT_CHECK_HEAD = False


class Crawler:
    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        session: Session = None,
        timeout: int = DEFAULT_TIMEOUT,
        check_head: bool = DEFAULT_CHECK_HEAD,
    ):
        self.user_agent = user_agent
        self.requester = Requester(user_agent=user_agent, session=session)

        self.queue = queue.Queue()

        self.seen_urls = set()
        self.done_urls = set()

        self.timeout = timeout
        self.check_head = check_head

    def crawl_url(self, url: Hyperlink):
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

        except (ClientError, ServerError, WrongMIMEType):
            pass

        self.done_urls.add(url)

    def crawl(self, domain: str):
        domain = make_hyperlink(domain)
        self.queue.put(domain)

        while True:
            if self.seen_urls == self.done_urls and self.seen_urls != set():
                return self.render_results()

            try:
                url = self.queue.get(timeout=self.timeout)
            except queue.Empty:
                return self.render_results()

            if url in self.done_urls:
                continue

            self.crawl_url(url)

        return self.render_results()

    def render_results(self):
        results = {str(url) for url in self.done_urls}
        self.queue = queue.Queue()
        self.seen_urls = set()
        self.done_urls = set()
        return results
