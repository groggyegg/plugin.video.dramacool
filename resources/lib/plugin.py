import re
import sys
import urllib.parse


def urlparse():
    global domain, fullpath, path, query
    (scheme, netloc, path, params, query, fragment) = urllib.parse.urlparse(url)
    domain = f'{scheme}://{netloc}'
    fullpath = f'{path}?{query}' if query else path
    query = urllib.parse.parse_qs(query)


url = sys.argv[0] + sys.argv[2]
domain = None
handle = int(sys.argv[1])
path = None
routedict = {}
query = None
fullpath = None
urlparse()


def redirect(fullpath):
    global url
    url = url_for(fullpath)
    urlparse()
    run()


def route(pattern, **queries):
    def decorator(function):
        if function not in routedict:
            routedict[function] = [(pattern, queries)]
        else:
            routedict[function].append((pattern, queries))

        return function

    return decorator


def run():
    for function, patterns in routedict.items():
        for pattern, queries in patterns:
            match = re.fullmatch(pattern, path)

            if match:
                kwargs = match.groupdict()

                for field, value in queries.items():
                    if isinstance(value, str):
                        if field in query:
                            for string in query[field]:
                                match = re.fullmatch(value, string)

                                if match:
                                    kwargs.update(match.groupdict())
                                else:
                                    break
                        else:
                            match = None
                            break
                    elif isinstance(value, bool) and ((value and field not in query) or (not value and field in query)):
                        match = None
                        break

                if match:
                    function(**kwargs)
                    return


def url_for(fullpath):
    return domain + fullpath
