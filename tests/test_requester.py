import pytest
from flask import abort
from flask import Flask

from simple_crawler.requester import ClientError
from simple_crawler.requester import Requester
from simple_crawler.requester import ServerError
from simple_crawler.requester import WrongMIMEType
from tests.conftest import WebServer

USER_AGENT = "TestAgent"

MOCK_URL = "https://www.example.com"
MOCK_BODY = "<html><body><h1>hello world</h1></body></html"


@pytest.fixture
def requester():
    requester = Requester(user_agent=USER_AGENT)
    return requester


@pytest.fixture(scope="module")
def requester_server():
    app = Flask("test")
    server = WebServer(app)

    @server.app.route("/")
    def index():
        return MOCK_BODY

    @server.app.route("/error/<int:code>")
    def error(code):
        return abort(code)

    @server.app.route("/mime/<group>/<name>")
    def mime(group, name):
        return MOCK_BODY, 200, {"Content-Type": f"{group}/{name}"}

    with server.run():
        yield server


@pytest.mark.parametrize("method, text", [("GET", MOCK_BODY), ("HEAD", "")])
def test_requester_request_200(method, text, requester, requester_server):
    response = requester.request(method, requester_server.url + "/", mime_types=("text/html",))
    assert response.text == text
    assert response.status_code == 200
    assert response.reason == "OK"
    assert "text/html" in response.headers["Content-Type"]


def test_requester_head_and_get_request_200(requester, requester_server):
    response = requester(requester_server.url + "/", check_head_first=True)
    assert response.text == MOCK_BODY
    assert response.status_code == 200
    assert response.reason == "OK"
    assert "text/html" in response.headers["Content-Type"]


@pytest.mark.parametrize("code, exc", [(400, ClientError), (404, ClientError), (500, ServerError)])
def test_requester_get_request_raises_error(requester, code, exc, requester_server):
    with pytest.raises(exc):
        requester(requester_server.url + f"/error/{code}", check_head_first=False)


@pytest.mark.parametrize("check_head", [True, False])
def test_requester_get_request_different_mime_type(requester, requester_server, check_head):
    response = requester(
        requester_server.url + "/mime/image/png",
        mime_types=("image/png",),
        check_head_first=check_head,
    )
    assert response.text == MOCK_BODY
    assert response.status_code == 200
    assert response.reason == "OK"
    assert "image/png" in response.headers["Content-Type"]


@pytest.mark.parametrize("check_head", [True, False])
def test_requester_get_request_mime_type_error(requester, check_head, requester_server):
    with pytest.raises(WrongMIMEType):
        requester(requester_server.url + "/mime/image/png", check_head_first=check_head)
