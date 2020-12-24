import pytest
import responses

from web_crawler.requester import ClientError
from web_crawler.requester import Requester
from web_crawler.requester import ServerError
from web_crawler.requester import WrongMIMEType

USER_AGENT = "TestAgent"

MOCK_URL = "https://www.example.com"
MOCK_BODY = "<html><body><h1>hello world</h1></body></html"


@pytest.fixture
def requester():
    requester = Requester(user_agent=USER_AGENT)
    return requester


# https://github.com/getsentry/responses
@responses.activate
@pytest.mark.parametrize("method", ["GET", "HEAD"])
def test_requester_request_200(method, requester):
    responses.add(
        getattr(responses, method),
        MOCK_URL,
        body=MOCK_BODY,
        status=200,
        content_type="text/html",
    )
    response = requester.request(method, MOCK_URL, mime_types=("text/html",))
    assert response.text == MOCK_BODY
    assert response.status_code == 200
    assert response.reason == "OK"
    assert "text/html" in response.headers["Content-Type"]


@responses.activate
def test_requester_head_and_get_request_200(requester):
    responses.add(responses.HEAD, MOCK_URL, status=200, content_type="text/html")
    responses.add(responses.GET, MOCK_URL, body=MOCK_BODY, status=200, content_type="text/html")
    response = requester(MOCK_URL, check_head_first=True)
    assert response.text == MOCK_BODY
    assert response.status_code == 200
    assert response.reason == "OK"
    assert "text/html" in response.headers["Content-Type"]


@responses.activate
def test_requester_get_request_4xx_error(requester):
    responses.add(
        responses.GET,
        MOCK_URL,
        body=MOCK_BODY,
        status=400,
    )
    with pytest.raises(ClientError):
        requester(MOCK_URL, check_head_first=False)


@responses.activate
def test_requester_get_request_5xx_error(requester):
    responses.add(
        responses.GET,
        MOCK_URL,
        body=MOCK_BODY,
        status=500,
    )
    with pytest.raises(ServerError):
        requester(MOCK_URL, check_head_first=False)


@responses.activate
def test_requester_get_request_different_mime_type_check_head(requester):
    responses.add(responses.HEAD, MOCK_URL, status=200, content_type="text/html")
    responses.add(
        responses.GET,
        MOCK_URL,
        status=200,
        content_type="text/html",
        body=MOCK_BODY,
    )
    response = requester(MOCK_URL, mime_types=("text/html",), check_head_first=True)
    assert response.text == MOCK_BODY
    assert response.status_code == 200
    assert response.reason == "OK"
    assert "text/html" in response.headers["Content-Type"]


@responses.activate
def test_requester_get_request_different_mime_type(requester):
    responses.add(responses.GET, MOCK_URL, status=200, content_type="image/png", body=MOCK_BODY)
    response = requester(MOCK_URL, mime_types=("image/png",), check_head_first=False)
    assert response.text == MOCK_BODY
    assert response.status_code == 200
    assert response.reason == "OK"
    assert "image/png" in response.headers["Content-Type"]


@responses.activate
def test_requester_get_request_mime_type_error_check_head(requester):
    responses.add(responses.HEAD, MOCK_URL, status=200, content_type="image/png")
    with pytest.raises(WrongMIMEType):
        requester(MOCK_URL, check_head_first=True)


@responses.activate
def test_requester_get_request_mime_type_error(requester):
    responses.add(responses.GET, MOCK_URL, status=200, content_type="image/png")
    with pytest.raises(WrongMIMEType):
        requester(MOCK_URL, check_head_first=False)
