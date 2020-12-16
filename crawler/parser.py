import urllib.parse
from html.parser import HTMLParser
from typing import Set


class HyperlinkReference:
    """
    a representation of a Hyperlink REFerence (href)
    """

    def __init__(self, link: str):
        if not isinstance(link, str):
            raise TypeError("href links need to be strings")

        # split is the core element we want to build class around
        normalised_link = urllib.parse.urljoin("/", link)
        scheme, netloc, path, query, fragment = urllib.parse.urlsplit(normalised_link)

        self.scheme = scheme.lower()
        self.netloc = netloc.lower().removesuffix(".")
        self.path = urllib.parse.quote(path, "/%") or "/"
        self.query = urllib.parse.quote_plus(query, ":&=")
        self.fragment = fragment

    def __str__(self):
        components = (self.scheme, self.netloc, self.path, self.query, self.fragment)
        return urllib.parse.urlunsplit(components)

    def __repr__(self):
        return f'href="{self}"'

    def __eq__(self, other):
        return str(self) == other

    def __hash__(self):
        return hash(repr(self))

    @property
    def is_absolute(self) -> bool:
        """all links that start with a scheme (e.g. https) are absolute"""
        return bool(self.scheme)

    @property
    def is_relative(self) -> bool:
        """all links that don't start with a scheme (e.g. https) are relative"""
        return not self.is_absolute

    def join(self, host: str):
        """
        bind a href to a host if possible (e.g. /example -> https://www.example.com/example)
        :param host: (str) an
        :return:
        """
        resolution = urllib.parse.urljoin(host, str(self))
        return HyperlinkReference(resolution)


class AnchorTagParser(HTMLParser):
    """
    Simple HTML parser that will take in HTML and get all the HREF values (links) from <a> tags
    docs: https://docs.python.org/3/library/html.parser.html

    * On instantiation this parser will create a set of found_links
    * When this parser is fed (via `feed`) a snippet of HTML it will save HREF links to found_links
    """

    def __init__(self):
        # init parent
        super().__init__()

        # create set of links found
        self.found_links = list()

    def handle_starttag(self, tag: str, attrs: list) -> None:
        # https://docs.python.org/3/library/html.parser.html#html.parser.HTMLParser.handle_starttag
        # HTMLParser manages lowercase for us

        # grab only a tags
        if tag == "a":
            for attr, value in attrs:
                # grab only hrefs
                if attr == "href":
                    self.found_links.append(value)

    def error(self, message: str) -> None:
        # ignore errors for now
        # assumption is that all production websites will have working (and therefore parsable) HTML
        pass


def get_unique_links_from_html(html: str) -> Set[str]:
    """
    * This function will find all <a> tags in a HTML snippet
    * It will grab all href attributes in the <a> tags
    * It will return a list of values assigned to href attribute

    :param html: (str) a html snippet
    :return: (set) a set of links found in all href attributes
    """
    parser = AnchorTagParser()
    parser.feed(html)
    return set(parser.found_links)
