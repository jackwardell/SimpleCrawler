import urllib.parse
from typing import Iterable
from typing import Union

from web_crawler.url_normalisation import normalise_authority
from web_crawler.url_normalisation import normalise_fragment
from web_crawler.url_normalisation import normalise_kwargs
from web_crawler.url_normalisation import normalise_path
from web_crawler.url_normalisation import normalise_query
from web_crawler.url_normalisation import normalise_scheme
from web_crawler.url_normalisation import normalise_url


class Hyperlink:
    """
    a representation of a Hyperlink REFerence (href)
    """

    __slots__ = "url", "_input_url"

    def __init__(self, link: str):
        # split is the core element we want to build class around
        self._input_url = link
        self.url = normalise_url(link)

    @property
    def components(self) -> urllib.parse.SplitResult:
        return urllib.parse.urlsplit(self._input_url)

    @property
    def scheme(self) -> str:
        return normalise_scheme(self.components.scheme)

    @property
    def authority(self) -> str:
        return normalise_authority(self.components.netloc)

    @property
    def path(self) -> str:
        return normalise_path(self.components.path)

    @property
    def query(self) -> str:
        return normalise_query(self.components.query)

    @property
    def fragment(self) -> str:
        return normalise_fragment(self.components.fragment)

    @property
    def domain(self):
        """this is the scheme and authority e.g. www.example.com"""
        scheme, authority, *_ = self.components
        return Hyperlink(urllib.parse.urlunsplit((scheme, authority, "", "", "")))

    def trim(
        self,
        scheme: bool = False,
        authority: bool = False,
        path: bool = False,
        query: bool = False,
        fragment: bool = False,
    ):
        """trim one (or more) of the elements off a href"""
        _scheme, _authority, _path, _query, _fragment = self.components
        # empty elements if trimmed
        url = urllib.parse.urlunsplit(
            (
                _scheme if not scheme else "",
                _authority if not authority else "",
                _path if not path else "",
                _query if not query else "",
                _fragment if not fragment else "",
            )
        )
        return Hyperlink(url)

    def with_path(self, path):
        """join path to self as base url"""
        return Hyperlink(self.domain.url + path)

    def __str__(self):
        return self.url

    def __repr__(self):
        return f'HREF("{self.url}")'

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.url == other.url

    def __hash__(self):
        return hash(repr(self))

    def __add__(self, other):
        return Hyperlink(self._input_url + str(other))

    def __truediv__(self, other):
        return Hyperlink(self._input_url + "/" + str(other))

    @property
    def is_absolute(self) -> bool:
        """all links that start with a scheme (e.g. https) are absolute"""
        return bool(self.scheme)

    @property
    def is_relative(self) -> bool:
        """all links that don't start with a scheme (e.g. https) are relative"""
        return not self.is_absolute

    def join(self, base_url: Union[str, "Hyperlink"]):
        """
        bind a href to a base_url if possible (e.g. /example -> https://www.example.com/example)

        :param base_url: (str) an base_url like https://www.example.com
        :return: Hyperlink bound to an base_url
        """
        base_url = make_hyperlink(base_url)
        resolution = urllib.parse.urljoin(base_url._input_url, self._input_url)
        return make_hyperlink(resolution)

    # @classmethod
    # def make(cls, link: str):
    #     """
    #     factory method for creating Hyperlinks
    #
    #     :param link: (str) any link/uri
    #     :return: (Hyperlink) an instance of hyperlink
    #     """
    #     if isinstance(link, cls):
    #         return link
    #
    #     if not isinstance(link, str):
    #         raise TypeError("href links need to be strings")
    #
    #     return cls(link)


# make_hyperlink = Hyperlink.make


def make_hyperlink(link: Union[str, Hyperlink]) -> Hyperlink:
    """
    factory method for creating Hyperlinks

    :param link: (str) any link/uri
    :return: (Hyperlink) an instance of hyperlink
    """
    if isinstance(link, Hyperlink):
        return link

    if not isinstance(link, str):
        raise TypeError("href links need to be strings")

    return Hyperlink(link)


class HyperlinkSet:
    """
    a set for hyperlink references that allows for simple transformations
    """

    def __init__(self, collection: set = None):
        self.collection = collection or set()

    def __len__(self):
        return len(self.collection)

    # def __getitem__(self, item):
    #     return self.collection[item]

    def __iter__(self):
        return iter(self.collection)

    def __contains__(self, item):
        return item in self.collection

    def add(self, link):
        if not isinstance(link, Hyperlink):
            raise TypeError("link must be a Hyperlink")

        self.collection.add(link)

    def __str__(self):
        return str(self.collection)

    def __repr__(self):
        return repr(self.collection)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.collection == other.collection

    def is_empty(self):
        return len(self.collection) == 0

    def is_not_empty(self):
        return not self.is_empty()

    # def dedupe(self):
    #     """
    #     remove all dupes and then create new instance of self
    #
    #     :return: new instance of HyperlinkReferenceCollection that is deduped
    #     """
    #     # quickest way to dedupe while retaining order
    #     return HyperlinkSet(list(dict.fromkeys(self.collection)))

    def join_all(self, base_url: Union[str, Hyperlink]):
        """
        apply join to all items in the collection and return a collection with those values

        :param base_url: (str) host to apply join to on HyperlinkReference
        :return: new instance of HyperlinkReferenceCollection that has entries all joined

        todo: base_url to Hyperlink
        """
        base_url = make_hyperlink(base_url)
        return HyperlinkSet({link.join(base_url) for link in self.collection})

    def filter_by(self, **kwargs):
        """
        apply filter_by to all items, filtering by: scheme, authority, path, query, fragment

        e.g. links.filter_by(scheme='https')

        :param kwargs: any of: scheme, authority, path, query, fragment = <some value>
        :return: new instance of HyperlinkReferenceCollection that has entries filtered
        """
        kwargs = normalise_kwargs(**kwargs)
        results = set()
        for link in self.collection:
            if all([getattr(link, k) == v for k, v in kwargs.items()]):
                results.add(link)
        return HyperlinkSet(results)

    def trim(self, **kwargs):
        return HyperlinkSet({href.trim(**kwargs) for href in self.collection})

    # @classmethod
    # def make(cls, links: set = None):
    #     """
    #     factory method for creating Hyperlinks
    #
    #     :param links: (list) any list of link/uri
    #     :return: (HyperlinkCollection) an instance of hyperlink collection
    #     """
    #     if links is None:
    #         return cls()
    #
    #     if not isinstance(links, set):
    #         raise TypeError("href links needs to be a list")
    #
    #     for link in links:
    #         if not isinstance(link, Hyperlink):
    #             raise TypeError("links must all be Hyperlink objects")
    #
    #     return cls(links)


def make_hyperlink_set(links: Iterable = None) -> HyperlinkSet:
    """
    factory method for creating Hyperlinks

    :param links: (list) any list of link/uri
    :return: (HyperlinkCollection) an instance of hyperlink collection
    """
    if links is None:
        return HyperlinkSet()

    if not isinstance(links, Iterable):
        raise TypeError("links must be iterable")

    results = set()
    for link in links:
        if not isinstance(link, (Hyperlink, str)):
            raise TypeError("links must all be Hyperlink objects")
        else:
            results.add(make_hyperlink(link))

    return HyperlinkSet(results)
