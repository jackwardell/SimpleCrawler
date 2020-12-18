import urllib.parse

from crawler.url_normalisation import normalise_kwargs
from crawler.url_normalisation import normalise_url


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
