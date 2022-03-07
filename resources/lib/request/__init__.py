from xbmclib import *

import os
import re
import requests

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
            super().__init__()
            self.feed(text)
            return self.close()

_addon = Addon()
_domains = ('watchasian.sh', 'watchasian.so', 'dramacool.sk')
_session = requests.Session()
_tempfile = os.path.join(translatePath(_addon.getAddonInfo('path')), 'resources/data/tempfile')


def get(path, subdomain=''):
    if subdomain:
        subdomain = subdomain + '.'

    for domain in _domains:
        response = _session.get(f'https://{subdomain}{domain}{path}')

        if response.status_code == 200:
            return response.text


def parse(path, parser, **kwargs):
    return parser(**kwargs).parse(get(path))


def subtitle(url):
    match = re.search('&sub=([^&]+)', url)

    if match:
        text = get(f'/player/sub/index.php?id={match.group(1)}', 'embed')

        if text:
            webvtt = text.replace('\ufeffWEBVTT\r\n\r\n', '', 1).split('\r\n\r\n')

            with open(_tempfile, 'w') as o:
                for counter, text in enumerate(webvtt, start=1):
                    o.write(f'{counter}\r\n{text}\r\n\r\n')

                return _tempfile
        else:
            Dialog().notification(_addon.getLocalizedString(33503), '')
