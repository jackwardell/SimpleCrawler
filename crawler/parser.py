from html.parser import HTMLParser
from typing import Set


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
