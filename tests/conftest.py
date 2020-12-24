import logging
import threading

import pytest
from flask import Flask


def make_html(body: str) -> str:
    """make a html doc by passing data to appear in <body> tag"""
    return f"<html><head></head><body>{body}</body></html>"


def make_a_tag(path: str) -> str:
    """make a <a> tag with path as HREF value"""
    return f'<a href="{path}">another link</a>'


def make_a_tags(paths: list) -> str:
    """make multiple <a> tags (via `make_a_tag`) seperated by <br> tags"""
    return "<br>".join([make_a_tag(path) for path in paths])


log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)


class WebServer(threading.Thread):
    HOST = "0.0.0.0"
    PORT = 9999

    def __init__(self, app):
        super(WebServer, self).__init__(
            target=app.run, kwargs={"host": self.HOST, "port": self.PORT}, daemon=True
        )

    @property
    def url(self):
        return f"http://{self.HOST}:{self.PORT}"


@pytest.fixture(scope="module")
def server():
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

    threaded_webserver = WebServer(app)

    return threaded_webserver
