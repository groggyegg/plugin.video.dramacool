"""
    MIT License

    Copyright (c) 2020 groggyegg

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
"""

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
