import doctest


def normalise_scheme(scheme: str) -> str:
    """
    normalise scheme (e.g. https)

    :param scheme: (str) https, http, ftp, etc
    :return: (str) lower case scheme

    >>> normalise_scheme('')
    ''
    >>> normalise_scheme('https')
    'https'
    >>> normalise_scheme('HTTPS')
    'https'
    """
    scheme = scheme.lower()
    return scheme


if __name__ == "__main__":
    doctest.testmod()
