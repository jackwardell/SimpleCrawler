import urllib.parse
from html.parser import HTMLParser

from .url_normalisation import normalise_kwargs
from .url_normalisation import normalise_url


class Hyperlink:
    """
    a representation of a Hyperlink REFerence (href)
    """

    __slots__ = "url"

    def __init__(self, link: str):
        # split is the core element we want to build class around
        self.url = link

    @property
    def components(self) -> urllib.parse.SplitResult:
        return urllib.parse.urlsplit(self.url)

    @property
    def scheme(self) -> str:
        return self.components.scheme

    @property
    def authority(self) -> str:
        return self.components.netloc

    @property
    def path(self) -> str:
        return self.components.path

    @property
    def query(self) -> str:
        return self.components.query

    @property
    def fragment(self) -> str:
        return self.components.fragment

    def __str__(self):
        return self.url

    def __repr__(self):
        return f'HREF("{self.url}")'

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.url == other.url

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
        host = normalise_url(host)
        resolution = urllib.parse.urljoin(host, self.url)
        return make_hyperlink(resolution)

    @classmethod
    def make(cls, link: str):
        """
        factory method for creating Hyperlinks

        :param link: (str) any link/uri
        :return: (Hyperlink) an instance of hyperlink
        """
        if not isinstance(link, str):
            raise TypeError("href links need to be strings")

        normalised_link = normalise_url(link)
        return cls(normalised_link)


make_hyperlink = Hyperlink.make


class HyperlinkCollection:
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
        """
        remove all dupes and then create new instance of self

        :return: new instance of HyperlinkReferenceCollection that is deduped
        """
        # quickest way to dedupe while retaining order
        return HyperlinkCollection(list(dict.fromkeys(self.collection)))

    def join_all(self, host: str):
        """
        apply join to all items in the collection and return a collection with those values

        :param host: (str) host to apply join to on HyperlinkReference
        :return: new instance of HyperlinkReferenceCollection that has entries all joined
        """
        return HyperlinkCollection([link.join(host) for link in self.collection])

    def filter_by(self, **kwargs):
        """
        apply filter_by to all items, filtering by: scheme, authority, path, query, fragment

        e.g. links.filter_by(scheme='https')

        :param kwargs: any of: scheme, authority, path, query, fragment = <some value>
        :return: new instance of HyperlinkReferenceCollection that has entries filtered
        """
        kwargs = normalise_kwargs(**kwargs)
        results = []
        for link in self.collection:
            if all([getattr(link, k) == v for k, v in kwargs.items()]):
                results.append(link)
        return HyperlinkCollection(results)


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
