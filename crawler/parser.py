from html.parser import HTMLParser

from .hyperlink import HyperlinkCollection
from .hyperlink import make_hyperlink


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
        self.found_links = HyperlinkCollection()

    def handle_starttag(self, tag: str, attrs: list) -> None:
        # https://docs.python.org/3/library/html.parser.html#html.parser.HTMLParser.handle_starttag
        # HTMLParser manages lowercase for us

        # grab only a tags
        if tag == "a":
            for attr, value in attrs:
                # grab only hrefs
                if attr == "href":
                    href = make_hyperlink(value)
                    self.found_links.append(href)

    def error(self, message: str) -> None:
        # ignore errors for now
        # assumption is that all production websites will have working (and therefore parsable) HTML
        pass


def get_hrefs_from_html(html: str, unique: bool = False) -> HyperlinkCollection:
    """
    * This function will find all <a> tags in a HTML snippet (via `AnchorTagParser`)
    * It will grab all href attributes in the <a> tags (as `HyperlinkReference` objects)
    * If unique=True, it will remove duplicate HyperlinkReference (`via dict.from_keys`)
    * It will return a list of HyperlinkReference objects

    :param html: (str) a html snippet
    :param unique: (bool) whether the retuning list should include duplicate hrefs
    :return: (list) a list of links found in all href attributes
    """
    parser = AnchorTagParser()
    parser.feed(html)
    if unique is True:
        return parser.found_links.dedupe()
    elif unique is False:
        return parser.found_links
    else:
        raise TypeError("unique must be True or False")
