import logging
import threading
from contextlib import contextmanager
from typing import Iterable

import pytest
from flask import Flask
from werkzeug.serving import make_server

from simple_crawler.hyperlink import make_hyperlink


def make_html(body: str) -> str:
    """make a html doc by passing data to appear in <body> tag"""
    return f"<html><head></head><body>{body}</body></html>"


def make_a_tag(path: str) -> str:
    """make a <a> tag with path as HREF value"""
    return f'<a href="{path}">another link</a>'


def make_a_tags(paths: Iterable[str]) -> str:
    """make multiple <a> tags (via `make_a_tag`) seperated by <br> tags"""
    return "<br>".join([make_a_tag(path) for path in paths])


def make_html_from_links(paths: Iterable[str]) -> str:
    """make a html doc from a list of a tags"""
    return make_html(make_a_tags(paths))


log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)


class WebServer:
    HOST = "0.0.0.0"
    PORT = 9999

    def __init__(self, app):
        self.app = app

    @contextmanager
    def run(self):
        webserver = make_server(self.HOST, self.PORT, self.app, threaded=True)
        thread = threading.Thread(target=webserver.serve_forever, daemon=True)
        thread.start()
        try:
            yield self
        finally:
            webserver.shutdown()
            thread.join()

    @property
    def url(self):
        return f"http://{self.HOST}:{self.PORT}"

    @property
    def href(self):
        return make_hyperlink(self.url)


@pytest.fixture(scope="function")
def server():
    app = Flask("test")
    return WebServer(app)
