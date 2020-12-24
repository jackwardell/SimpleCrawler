import logging
import threading

import pytest
from flask import Flask

from tests.conftest import make_a_tags
from tests.conftest import make_html
from web_crawler.crawler import Crawler
from web_crawler.hyperlink import make_hyperlink
from web_crawler.hyperlink import make_hyperlink_collection

log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

HOST = "0.0.0.0"
PORT = 9999
URL = f"http://{HOST}:{PORT}"


@pytest.fixture(scope="module")
def app():
    app = Flask("test")

    @app.route("/")
    def index():
        tags = ["/", "/hello", "/world"]
        return make_html(make_a_tags(tags))

    @app.route("/hello")
    def hello():
        tags = ["/", "/hello/world", "/world"]
        return make_html(make_a_tags(tags))

    @app.route("/hello/world")
    def hello_world():
        tags = ["/", "/hello"]
        return make_html(make_a_tags(tags))

    @app.route("/world")
    def world():
        tags = ["/", "/hello", "/world"]
        return make_html(make_a_tags(tags))

    threading.Thread(target=app.run, kwargs={"host": HOST, "port": PORT}, daemon=True).start()


def test_crawler(app):
    crawler = Crawler(timeout=1)
    found_urls = crawler.crawl(URL)
    urls_to_find = make_hyperlink_collection(
        [make_hyperlink(url) for url in ["/", "/hello", "/hello/world", "/world"]]
    ).join_all(URL)
    assert found_urls == set(urls_to_find)
