import requests

from web_crawler.parser import get_hrefs_from_html


class Crawler:
    def __init__(self):
        self.todo_urls = set()

    def crawl_url(self, url):
        self.todo_urls.remove(url)
        return get_hrefs_from_html(requests.get(url).text)

    def crawl(self, url):
        while self.todo_urls != set():
            found_urls = self.crawl_url(url)
            for url in found_urls:
                self.todo_urls.add(url)
