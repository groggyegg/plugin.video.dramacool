from re import fullmatch

import collections
import sys
import urllib.parse

handle = int(sys.argv[1])
path = None
pathquery = None
query = None
url = None

_domain = None
_routedict = collections.OrderedDict()


def redirect(pathquerystring):
    _url_parse(_domain + pathquerystring)

    for routes in _routedict.values():
        for (function, patterns) in routes.items():
            for pattern in patterns:
                match = fullmatch(pattern, pathquery)

                if match is not None:
                    function(**match.groupdict())
                    return


def route(pattern, order=0):
    if order not in _routedict:
        _routedict[order] = {}

    def decorator(function):
        if function not in _routedict[order]:
            _routedict[order][function] = [pattern]
        else:
            _routedict[order][function].append(pattern)

        return function

    return decorator


def run():
    _url_parse(sys.argv[0] + sys.argv[2])
    redirect(pathquery)


def url_for(pathquerystring):
    return _domain + pathquerystring


def _url_parse(urlstring):
    global _domain, path, pathquery, query, url

    url = urlstring
    (scheme, netloc, path, params, query, fragment) = urllib.parse.urlparse(url)
    pathquery = path + (f'?{query}' if query else '')
    query = urllib.parse.parse_qs(query)
    _domain = f'{scheme}://{netloc}'
