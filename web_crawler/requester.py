"""
module service that handles getting text data from web servers
"""
from typing import Iterable

import requests

from web_crawler.hyperlink import Hyperlink


class RequesterError(Exception):
    """Base exception for this service"""

    pass


class WrongMIMEType(RequesterError):
    """Wrong MIME type"""

    pass


class ClientError(RequesterError):
    """4xx HTTP status code"""

    pass


class ServerError(RequesterError):
    """5xx HTTP status code"""

    pass


class Requester:
    """this class maintains a request session and handles all logic RE getting text"""

    def __init__(self, session: requests.Session = None, user_agent: str = None):
        self.session = session or requests.Session()
        self.user_agent = user_agent

        if user_agent is not None:
            self.session.headers["User-Agent"] = self.user_agent

    def request(
        self,
        method: str,
        url: Hyperlink,
        mime_types: Iterable,
        follow_redirects: bool = True,
    ) -> requests.Response:
        """
        wrapper function around requests.request that handles some internal logic

        :param method: (str) GET, HEAD, etc (any HTTP method)
        :param url: (Hyperlink) a link to ping
        :param mime_types: (Iterable) a selection of mime-types that are acceptable
        :param follow_redirects (bool) whether or not to follow redirects
        :return: (str) the response text (e.g. the html)

        :raises: ClientError if 4xx from response
        :raises: ServerError if 5xx from response
        :raises: MimeTypeError if response MIME type doesn't match mime_types param
        """
        response = self.session.request(
            method, str(url), timeout=(2, 15), allow_redirects=follow_redirects
        )

        if str(response.status_code).startswith("4"):
            raise ClientError(f"{response.status_code} {response.reason}")

        if str(response.status_code).startswith("5"):
            raise ServerError(f"{response.status_code} {response.reason}")

        for mime_type in mime_types:
            if mime_type.lower() in response.headers["Content-Type"].lower():
                return response

        raise WrongMIMEType(f"{response.headers['Content-Type']} not in {mime_types}")

    def __call__(
        self,
        url: Hyperlink,
        mime_types: Iterable = ("text/html",),
        check_head_first: bool = True,
        follow_redirects: bool = True,
    ) -> requests.Response:
        """
        wrapper around self.request that allows the class to be callable
        and has default args

        :param url: (Hyperlink) url to go ping
        :param mime_types: (Iterable) acceptable mime types for response, defaults to "text/html"
        :param check_head_first: (bool) whether make a HEAD HTTP request before GET to see if mime type is acceptable
        :param follow_redirects (bool) whether or not to follow redirects
        :return: (str) the text

        :raises: ClientError if 4xx from response
        :raises: ServerError if 5xx from response
        :raises: MimeTypeError if response MIME type doesn't match mime_types param
        """
        if check_head_first:
            self.request("HEAD", url, mime_types, follow_redirects=follow_redirects)

        return self.request("GET", url, mime_types, follow_redirects=follow_redirects)
