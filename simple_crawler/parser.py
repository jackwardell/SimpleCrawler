"""
module for parsing HTML and getting out the links
"""
from html.parser import HTMLParser

from .hyperlink import HyperlinkSet
from .hyperlink import make_hyperlink
from .hyperlink import make_hyperlink_set


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
        self.found_links = make_hyperlink_set()

    def handle_starttag(self, tag: str, attrs: list) -> None:
        # https://docs.python.org/3/library/html.parser.html#html.parser.HTMLParser.handle_starttag
        # HTMLParser manages lowercase for us

        # grab only a tags
        if tag == "a":
            for attr, value in attrs:
                # grab only hrefs
                if attr == "href":
                    href = make_hyperlink(value)
                    self.found_links.add(href)

    def error(self, message: str) -> None:
        # ignore errors for now
        # assumption is that all production websites will have working (and therefore parsable) HTML
        pass


def get_hrefs_from_html(html: str) -> HyperlinkSet:
    """
    * This function will find all <a> tags in a HTML snippet (via `AnchorTagParser`)
    * It will grab all href attributes in the <a> tags (as `Hyperlink` objects)
    * It will return a HyperlinkSet object

    :param html: (str) a html snippet
    :return: (HyperlinkSet) a set of links found in all href attributes
    """
    parser = AnchorTagParser()
    parser.feed(html)
    return parser.found_links
