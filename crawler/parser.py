from html.parser import HTMLParser
from typing import Set


class AnchorTagParser(HTMLParser):
    def __init__(self):
        # init parent
        super().__init__()

        # create set of links found
        self.links_found = set()

    def handle_starttag(self, tag, attrs):
        # https://docs.python.org/3/library/html.parser.html#html.parser.HTMLParser.handle_starttag
        # HTMLParser manages lowercase for us
        if tag == "a":
            for attr, value in attrs:
                if attr == "href":
                    self.links_found.add(value)

    def error(self, message):
        pass


def get_links_from_html(html: str) -> Set[str]:
    parser = AnchorTagParser()
    parser.feed(html)
    return parser.links_found
