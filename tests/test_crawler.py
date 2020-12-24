from web_crawler.crawler import Crawler
from web_crawler.hyperlink import make_hyperlink
from web_crawler.hyperlink import make_hyperlink_collection


def test_crawler(server):
    server.start()

    crawler = Crawler(timeout=1)
    found_urls = crawler.crawl(server.url)
    urls_to_find = make_hyperlink_collection(
        [make_hyperlink(url) for url in ["/", "/hello", "/hello/world", "/world"]]
    ).join_all(server.url)
    assert found_urls == {str(url) for url in urls_to_find}
