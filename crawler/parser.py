import urllib.parse
from html.parser import HTMLParser


class HyperlinkReference:
    """
    a representation of a Hyperlink REFerence (href)
    """

    __slots__ = ("scheme", "netloc", "path", "query", "fragment")

    def __init__(self, link: str):
        if not isinstance(link, str):
            raise TypeError("href links need to be strings")

        # split is the core element we want to build class around
        normalised_link = urllib.parse.urljoin("/", link)
        scheme, netloc, path, query, fragment = urllib.parse.urlsplit(normalised_link)

        self.scheme = scheme.lower()
        self.netloc = netloc.lower().removesuffix(".")
        self.path = "/" + urllib.parse.quote(path, "/%").removeprefix("/")
        self.query = urllib.parse.quote_plus(query, ":&=")
        self.fragment = fragment

    def __str__(self):
        components = (self.scheme, self.netloc, self.path, self.query, self.fragment)
        return urllib.parse.urlunsplit(components)

    def __repr__(self):
        return f'HREF("{self}")'

    def __eq__(self, other):
        return isinstance(other, self.__class__) and repr(self) == repr(other)

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


class HyperlinkReferenceCollection:
    """
    a list for hyperlink references that allows for simple transformations
    """

    def __init__(self, collection: list = None):
        self.collection = collection or []

    def __len__(self):
        return len(self.collection)

    def __getitem__(self, item):
        return self.collection[item]

    def __iter__(self):
        return iter(self.collection)

    def __contains__(self, item):
        return item in self.collection

    def append(self, link):
        self.collection.append(link)

    def __str__(self):
        return str(self.collection)

    def __repr__(self):
        return repr(self.collection)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.collection == other.collection

    def dedupe(self):
        """remove all dupes and then create new instance of self"""
        # quickest way to dedupe while retaining order
        return HyperlinkReferenceCollection(list(dict.fromkeys(self.collection)))

    def join_all(self, host: str):
        return HyperlinkReferenceCollection([link.join(host) for link in self.collection])


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
        self.found_links = HyperlinkReferenceCollection()

    def handle_starttag(self, tag: str, attrs: list) -> None:
        # https://docs.python.org/3/library/html.parser.html#html.parser.HTMLParser.handle_starttag
        # HTMLParser manages lowercase for us

        # grab only a tags
        if tag == "a":
            for attr, value in attrs:
                # grab only hrefs
                if attr == "href":
                    href = HyperlinkReference(value)
                    self.found_links.append(href)

    def error(self, message: str) -> None:
        # ignore errors for now
        # assumption is that all production websites will have working (and therefore parsable) HTML
        pass


def get_hrefs_from_html(html: str, unique: bool = False) -> HyperlinkReferenceCollection:
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
