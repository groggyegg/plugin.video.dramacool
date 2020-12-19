import re
import sys
import urllib.parse


def redirect(full_path):
    global url
    url = url_for(full_path)
    urlparse()
    run()


def route(rule, **options):
    def decorator(function):
        if function in routedict:
            routedict[function].append((rule, options))
        else:
            routedict[function] = [(rule, options)]

        return function

    return decorator


def run():
    for function, routes in routedict.items():
        for rule, options in routes:
            match = re.fullmatch(rule, path)

            if match:
                kwargs = match.groupdict()

                for name, value in options.items():
                    if isinstance(value, str):
                        if name in query:
                            for string in query[name]:
                                match = re.fullmatch(value, string)

                                if match:
                                    kwargs.update(match.groupdict())
                                else:
                                    break
                        else:
                            match = None
                            break
                    elif isinstance(value, bool) and ((value and name not in query) or (not value and name in query)):
                        match = None
                        break

                if match:
                    function(**kwargs)
                    return


def url_for(full_path):
    return base_url + full_path


def urlparse():
    global base_url, full_path, path, query
    (scheme, netloc, path, params, query, fragment) = urllib.parse.urlparse(url)
    base_url = f'{scheme}://{netloc}'
    full_path = f'{path}?{query}' if query else path
    query = urllib.parse.parse_qs(query)


base_url = None
full_path = None
handle = int(sys.argv[1])
path = None
query = None
routedict = {}
url = sys.argv[0] + sys.argv[2]
urlparse()
