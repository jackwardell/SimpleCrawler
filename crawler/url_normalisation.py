"""
module for normalising urls

why?
    a web crawler might encounter urls that look different
    but are otherwise the same

    e.g.
    * HTTPS://:@WWW.EXAMPLE.COM?greeting=hello world
    * https://www.example.com/?greeting=hello+world

    these are the same and although many web devs building hrefs won't be
    make these mistakes, they can be encountered and need to be handled

"""
import doctest
import urllib.parse


def normalise_scheme(scheme: str) -> str:
    """
    normalise scheme (e.g. https)

    :param scheme: (str) https, http, ftp, etc
    :return: (str) lower case scheme

    >>> normalise_scheme('')
    ''
    >>> normalise_scheme('https')
    'https'
    >>> normalise_scheme('HTTPS')
    'https'
    """
    scheme = scheme.lower()
    return scheme


def normalise_host(host: str) -> str:
    """
    normalise host (e.g. localhost, www.google.com)

    :param host: (str) any host
    :return: (str) normalised lower case host

    >>> normalise_host('')
    ''
    >>> normalise_host('www.google.com')
    'www.google.com'
    >>> normalise_host('www.EXAMPLE.com')
    'www.example.com'
    >>> normalise_host('www.example.com.')
    'www.example.com'

    todo: idna?
    """
    host = host.lower()
    host = host.strip(".")
    return host


def normalise_userinfo(userinfo: str) -> str:
    """
    normalise userinfo (e.g. hello:world)
    NB: passwords are NOT recommended to be sent via clear text

    :param userinfo: (str) any defined user info, with username and/or password
    :return: (str) normalised user info

    >>> normalise_userinfo('')
    ''
    >>> normalise_userinfo('hello:world')
    'hello:world'
    >>> normalise_userinfo('hello:')
    'hello'
    >>> normalise_userinfo(':')
    ''
    """
    userinfo = userinfo.strip(":")
    return userinfo


def normalise_authority(authority: str) -> str:
    """
    normalise authority (e.g. hello:world@www.example.com)
    NB: urllib.parse wrongly calls this netloc, which is actually just www.example.com

    :param authority: (str) any authority with userinfo and/or netloc
    :return: (str) normalised authority

    >>> normalise_authority('')
    ''
    >>> normalise_authority('www.EXAMPLE.com')
    'www.example.com'
    >>> normalise_authority('hello@www.example.com')
    'hello@www.example.com'
    >>> normalise_authority('hello:@www.EXAMPLE.com')
    'hello@www.example.com'
    >>> normalise_authority('hello:world@www.example.com')
    'hello:world@www.example.com'
    >>> normalise_authority('@www.example.com')
    'www.example.com'
    >>> normalise_authority('www.example.com.')
    'www.example.com'

    # todo normalise port?
    """
    if authority == "":
        return authority

    if "@" in authority:
        userinfo, host = authority.split("@")
        userinfo = normalise_userinfo(userinfo)
    else:
        userinfo, host = "", authority

    host = normalise_host(host)
    if userinfo != "":
        authority = "@".join([userinfo, host])
    else:
        authority = host

    return authority


def normalise_path(path: str) -> str:
    """
    normalise a path (e.g. /hello/world)

    :param path: (str) url path
    :return: (str) a normalised path

    >>> normalise_path('')
    '/'
    >>> normalise_path('/hello/world')
    '/hello/world'
    >>> normalise_path('hello')
    '/hello'
    >>> normalise_path("hello world")
    '/hello%20world'
    """
    path = urllib.parse.quote(path, safe="/%")
    if not path.startswith("/"):
        path = "/" + path
    return path


def normalise_query(query: str) -> str:
    """
    normalise a query string (e.g. hello=world&world=hello)

    :param query: (str) query string
    :return: a normalised query string

    >>> normalise_query('')
    ''
    >>> normalise_query('hello=world')
    'hello=world'
    >>> normalise_query('hello=world&world=hello')
    'hello=world&world=hello'
    >>> normalise_query('greeting=hi there')
    'greeting=hi+there'

    # todo sort query params?
    """
    query = urllib.parse.quote_plus(query, safe=":&=")
    return query


def normalise_fragment(fragment: str) -> str:
    """
    normalise a fragment (e.g. #hello)
    NB: doesn't include #

    :param fragment: (str) some fragment
    :return: (str) a normalised fragment

    >>> normalise_fragment('')
    ''
    >>> normalise_fragment('hello')
    'hello'
    >>> normalise_fragment('hello:~world')
    'hello:~world'
    >>> normalise_fragment('hello world')
    'hello+world'
    >>> normalise_fragment('hello+world')
    'hello%2Bworld'
    >>> normalise_fragment("what's this?")
    'what%27s+this%3F'
    """
    fragment = urllib.parse.quote_plus(fragment, safe=":~")
    return fragment


def normalise_url(url: str) -> str:
    """
    normalise any url

    :param url: (str) any url to normalise
    :return: (str) normalised url

    >>> normalise_url('')
    '/'
    >>> normalise_url('www.EXAMPLE.com?hello=world')
    '/www.EXAMPLE.com?hello=world'
    >>> normalise_url('http://www.EXAMPLE.com?hello=world')
    'http://www.example.com/?hello=world'
    >>> normalise_url('http://@example.com#hello')
    'http://example.com/#hello'
    >>> normalise_url('http://hello:@example.com/hello/world?hello=world&world=hello#hi')
    'http://hello@example.com/hello/world?hello=world&world=hello#hi'
    >>> normalise_url("HTTPS://HELLO.WORLD@EXAMPLE.CO.UK/ hi there")
    'https://HELLO.WORLD@example.co.uk/%20hi%20there'
    """
    # split is the core element we want to build class around
    url = urllib.parse.urljoin("/", url)
    scheme, netloc, path, query, fragment = urllib.parse.urlsplit(url)
    components = (
        normalise_scheme(scheme),
        normalise_authority(netloc),
        normalise_path(path),
        normalise_query(query),
        normalise_fragment(fragment),
    )
    return urllib.parse.urlunsplit(components)


if __name__ == "__main__":
    doctest.testmod()
