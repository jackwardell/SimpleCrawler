from html.parser import HTMLParser
from typing import Set


class AnchorTagParser(HTMLParser):
    """
    Simple parser for HTML
    docs: https://docs.python.org/3/library/html.parser.html

    * On instantiation this parser will create a set of found links (via `links_found`)
    * When this parser is fed (via `feed`) a snippet of HTML it will save href links to found links

    """

    def __init__(self):
        # init parent
        super().__init__()

        # create set of links found
        self.links_found = set()

    def handle_starttag(self, tag, attrs):
        # https://docs.python.org/3/library/html.parser.html#html.parser.HTMLParser.handle_starttag
        # HTMLParser manages lowercase for us

        # grab only a tags
        if tag == "a":
            for attr, value in attrs:
                # grab only hrefs
                if attr == "href":
                    self.links_found.add(value)

    def error(self, message):
        pass


def get_links_from_html(html: str) -> Set[str]:
    """
    * This function will find all <a> tags in a HTML snippet
    * It will grab all href attributes in the <a> tags
    * It will return a list of values assigned to href attribute

    :param html: (str) a html snippet
    :return: (set) a set of links found in all href attributes
    """
    parser = AnchorTagParser()
    parser.feed(html)
    return parser.links_found
