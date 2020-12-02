import os
import re
import requests
import xbmcaddon
import xbmcvfs

_domains = ('https://watchasian.cc', 'https://dramacool.so', 'https://embed.watchasian.cc')
_session = requests.Session()
_tempfile = os.path.join(xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path')), 'resources/data/tempfile')


def get(pathquery):
    for domain in _domains:
        response = _session.get(domain + pathquery)

        if response.status_code == 200:
            return response.text

    return None


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
