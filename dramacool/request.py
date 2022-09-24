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

from abc import abstractmethod
from os.path import join
from re import compile, search

from bs4 import BeautifulSoup
from bs4.element import SoupStrainer, NavigableString
from pymaybe import maybe
from requests import Session
from requests.utils import requote_uri
from six.moves.urllib.parse import urlparse
from xbmcext import Dialog, getLocalizedString, getPath

__all__ = ['SubtitleRequest', 'DramaListRequest', 'DramaDetailRequest', 'DramaDetailRequest', 'RecentlyDramaRequest',
           'SearchRequest', 'EpisodeListRequest', 'ServerListRequest', 'StarListRequest', 'StarDramaRequest']


class Request(object):
    domains = 'watchasian.cx', 'www1.dramacool.ee'
    session = Session()
    tempfile = join(getPath(), 'resources/data/tempfile')

    def get(self, path):
        for domain in self.domains:
            response = self.session.get('https://{}{}'.format(domain, path), verify=False)

            if response.status_code == 200:
                return self.parse(response.text, path)

        raise ConnectionError(getLocalizedString(33504))

    @abstractmethod
    def parse(self, text, path):
        pass


class SubtitleRequest(Request):
    def get(self, url):
        match = search('&sub=([^&]+)', url)

        if match:
            response = self.session.get('https://embed.{}/player/sub/index.php?id={}'.format(self.domains[0], match.group(1)))

            if response.status_code == 200:
                return self.parse(response.text, url)
            else:
                Dialog().notification(getLocalizedString(33503), '')

    def parse(self, text, url):
        webvtt = text.replace('\ufeffWEBVTT\r\n\r\n', '', 1).split('\r\n\r\n')

        with open(self.tempfile, 'w') as o:
            for counter, text in enumerate(webvtt, start=1):
                o.write('{}\r\n{}\r\n\r\n'.format(counter, text))

            return self.tempfile


class DramaListRequest(Request):
    def get(self, path='/drama-list'):
        return super(DramaListRequest, self).get(path)

    def parse(self, text, path):
        soup = BeautifulSoup(text, 'html.parser', parse_only=SoupStrainer('li', {'data-genre': True}))
        return [a.attrs['href'] for a in soup.find_all('a') if 'href' in a.attrs]


class DramaDetailRequest(Request):
    def parse(self, text, path):
        soup = BeautifulSoup(text, 'html.parser', parse_only=SoupStrainer('div', {'class': 'details'}))
        poster = maybe(soup.find('img')).attrs['src'].or_none()
        title = soup.find('h1').text.strip()
        plot = ' '.join(p.text.strip() for p in soup.find_all(self.plot))
        country = maybe(soup.find('a', {'href': compile('^/country/')})).text.or_none()
        status = maybe(soup.find('a', {'href': compile('^/popular-')})).text.or_none()
        year = maybe(soup.find('a', {'href': compile('^/released-in-')})).text.or_none()
        genre = [a.text for a in soup.find_all('a', {'href': compile('^/genre/')})]
        return {'path': path, 'poster': requote_uri(poster) if poster else poster, 'title': title, 'plot': plot,
                'country': country, 'status': status, 'year': None if year == '0' else year, 'genre': genre}

    @staticmethod
    def plot(tag):
        return tag.name == 'p' and isinstance(tag.next, NavigableString)


class RecentlyDramaRequest(Request):
    def parse(self, text, path):
        soup = BeautifulSoup(text, 'html.parser', parse_only=SoupStrainer('ul', {'class': ['list-star', 'switch-block list-episode-item', 'pagination']}))
        return (self.episodes(soup.find('ul', {'class': ['list-star', 'switch-block list-episode-item']}, False)),
                self.pagination(soup.find('ul', {'class': 'pagination'}, False), path))

    @staticmethod
    def episodes(tag):
        return [(a.attrs['href'],
                 requote_uri(a.find('img').attrs['data-original']),
                 a.find('span', {'class': 'time'}).text,
                 "[{}] {} {}".format(a.find('span', {'class': 'type'}).text,
                                     a.find('h3').text,
                                     a.find('span', {'class': 'ep'}).text)) for a in tag.find_all('a')]

    @staticmethod
    def pagination(tag, path):
        page_links = ['first', 'previous', 'next', 'last']
        return [(urlparse(path).path + a.attrs['href'], next(filter(lambda class_: class_ in page_links, classes), None))
                for a, classes in iter((li.find('a'), li.attrs['class']) for li in maybe(tag).find_all('li', {'class': page_links}).or_else([]))]


class SearchRequest(RecentlyDramaRequest):
    @staticmethod
    def episodes(tag):
        return [(a.attrs['href'], a.find('h3').text, requote_uri(a.find('img').attrs['data-original'])) for a in maybe(tag).find_all('a').or_else([])]


class EpisodeListRequest(Request):
    def parse(self, text, path):
        soup = BeautifulSoup(text, 'html.parser', parse_only=SoupStrainer('ul', {'class': 'list-episode-item-2 all-episode'}))
        return [(a.attrs['href'], "[{}] {}".format(a.find('span', {'class': 'type'}).text, a.find('h3').text.strip())) for a in soup.find_all('a')]


class ServerListRequest(Request):
    def parse(self, text, path):
        soup = BeautifulSoup(text, 'html.parser', parse_only=SoupStrainer('div', {'class': 'block watch-drama'}))
        return (soup.find('h1').text,
                soup.find('a').attrs['href'],
                [(urlparse(li.attrs['data-video'], 'https').geturl(), li.next.strip()) for li in soup.find_all('li', {'data-video': compile('//')})])


class StarListRequest(RecentlyDramaRequest):
    @staticmethod
    def episodes(tag):
        return [(li.find_next('a').attrs['href'],
                 li.find_next('a', {'class': False}).text,
                 requote_uri(li.find_next('img').attrs['data-original']),
                 li.find_next('ul').text.strip()) for li in tag.find_all('li', recursive=False)]


class StarDramaRequest(Request):
    def parse(self, text, path):
        soup = BeautifulSoup(text, 'html.parser', parse_only=SoupStrainer('ul', {'class': 'list-episode-item'}))
        return [(a.attrs['href'], a.find_next('h3').text, requote_uri(a.find_next('img').attrs['data-original'])) for a in soup.find_all('a')]
