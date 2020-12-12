from re import fullmatch
from sys import argv
from urllib.parse import urlparse

import collections

handle = int(argv[1])
url = argv[0] + argv[2]
(scheme, netloc, path, params, query, fragment) = urlparse(url)
domain = f'{scheme}://{netloc}'
pathquery = f'{path}?{query}' if query else path
routedict = collections.OrderedDict()


def redirect(pathstring):
    global path, pathquery, query, url
    url = url_for(pathstring)
    (_, _, path, _, query, _) = urlparse(pathstring)
    pathquery = f'{path}?{query}' if query else path
    run()


def route(pattern, order=0):
    if order not in routedict:
        routedict[order] = {}

    def decorator(function):
        if function not in routedict[order]:
            routedict[order][function] = [pattern]
        else:
            routedict[order][function].append(pattern)

        return function

    return decorator


def run():
    for routes in routedict.values():
        for (function, patterns) in routes.items():
            for pattern in patterns:
                match = fullmatch(pattern, pathquery)

                if match is not None:
                    function(**match.groupdict())
                    return


def url_for(pathstring):
    return domain + pathstring
