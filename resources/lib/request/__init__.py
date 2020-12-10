from importlib import import_module
from inspect import isclass
from pathlib import Path
from pkgutil import iter_modules

import os
import re
import requests
import xbmcaddon
import xbmcvfs

try:
    import lxml.etree


    class Parser(object):
        def parse(self, text):
            return lxml.etree.HTML(text, lxml.etree.HTMLParser(target=self))

except ImportError:
    import html.parser


    class Parser(html.parser.HTMLParser):
        def error(self, message):
            pass

        def handle_data(self, data):
            self.data(data)

        def handle_endtag(self, tag):
            self.end(tag)

        def handle_starttag(self, tag, attrs):
            self.start(tag, dict(attrs))

        def parse(self, text):
            self.feed(text)
            return self.close()

_domains = ('https://watchasian.cc', 'https://dramacool.so', 'https://embed.watchasian.cc')
_parserdict = {}
_session = requests.Session()
_tempfile = os.path.join(xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path')), 'resources/data/tempfile')

for module_info in iter_modules([Path(__file__).parent]):
    module = import_module(f"{__name__}.{module_info.name}")

    for attribute_name in dir(module):
        attribute = getattr(module, attribute_name)

        if isclass(attribute) and issubclass(attribute, Parser):
            _parserdict[attribute_name] = attribute


def get(path):
    for domain in _domains:
        response = _session.get(domain + path)

        if response.status_code == 200:
            return response.text


def parse(path, classname, **kwargs):
    for name, parser in _parserdict.items():
        if classname == name:
            return parser(**kwargs).parse(get(path))


def subtitle(url):
    match = re.search('&sub=([^&]+)', url)

    if match:
        text = get(f'/player/sub/index.php?id={match.group(1)}')

        if text is not None:
            webvtt = text.replace('\ufeffWEBVTT\r\n\r\n', '', 1).split('\r\n\r\n')

            with open(_tempfile, 'w') as o:
                for counter, text in enumerate(webvtt, start=1):
                    o.write(f'{counter}\r\n{text}\r\n\r\n')

                return _tempfile, 0

        return None, 33503

    return None, 0
