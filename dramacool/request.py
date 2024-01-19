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

from __future__ import unicode_literals

from re import compile, search

from bs4 import BeautifulSoup, NavigableString, SoupStrainer
from requests import Session
from requests.exceptions import ConnectionError
from xbmcext import getLocalizedString, getSettingString, urlparse
from xbmcext.pymaybe import maybe


class Request(object):
    domains = getSettingString('domain1') or 'watchasian.sk', getSettingString('domain2')
    session = Session()

    @classmethod
    def get(cls, path):
        for domain in cls.domains:
            if domain:
                try:
                    response = cls.session.get('https://{}{}'.format(domain, path))

                    if response.status_code == 200:
                        return response.text
                except:
                    pass

        raise ConnectionError(getLocalizedString(33504))

    @classmethod
    def drama_detail(cls, path):
        doc = BeautifulSoup(cls.get(path), 'html.parser', parse_only=SoupStrainer('div', {'class': 'details'}))
        return {'path': path,
                'poster': urlparse(doc.find('img').attrs['src']).path,
                'title': doc.find('h1').text.strip(),
                'plot': ' '.join(p.text.strip() for p in doc.find_all(lambda element: element.name == 'p' and isinstance(element.next, NavigableString))),
                'country': cls.country(doc.find('a', {'href': compile('^/country/')}).text),
                'status': cls.status(doc.find('a', {'href': compile('^/popular-')}).text),
                'year': int(maybe(doc.find('a', {'href': compile('^/released-in-')}, string=compile('\\d+'))).text.or_else('0')),
                'genre': cls.genre({a.text for a in doc.find_all('a', {'href': compile('^/genre/')})})}

    @classmethod
    def country(cls, country):
        return {'Korean': 33700,
                'Japanese': 33701,
                'Taiwanese': 33702,
                'Hong Kong': 33703,
                'Chinese': 33704,
                'American': 33705,
                'Other Asia': 33706,
                'Thailand': 33707,
                'Indian': 33708}[country]

    @classmethod
    def status(cls, status):
        return {'Ongoing': 33709, 'Completed': 33710, 'Upcoming': 33711}[status]

    @classmethod
    def genre(cls, genres):
        translation = {'Action': 33712,
                       'Adventure': 33713,
                       'Comedy': 33714,
                       'Crime': 33715,
                       'Drama': 33716,
                       'Fantasy': 33717,
                       'Horror': 33718,
                       'Mystery': 33719,
                       'Romance': 33720,
                       'Sci-fi': 33721,
                       'Thriller': 33722}
        return sorted(translation[genre] for genre in genres if genre in translation)

    @classmethod
    def drama_detail_episode(cls, path):
        doc = BeautifulSoup(cls.get(path), 'html.parser', parse_only=SoupStrainer(['h1', 'ul']))
        title = doc.find('h1').text
        for a in doc.find('ul', {'class': 'list-episode-item-2 all-episode'}).find_all('a'):
            yield a.attrs['href'], '[COLOR orange]{}[/COLOR]'.format(title) if a.find('span', {'class': 'type'}).text == 'RAW' else title, int(maybe(search('Episode (\\d+)', a.find('h3').text)).group(1).or_else('0'))

    @classmethod
    def drama_list(cls, path):
        doc = BeautifulSoup(cls.get(path), 'html.parser', parse_only=SoupStrainer('li', {'data-genre': True}))
        return [a.attrs['href'] for a in doc.find_all('a')]

    @classmethod
    def list_star(cls, path):
        doc = BeautifulSoup(cls.get(path), 'html.parser', parse_only=SoupStrainer('ul', {'class': ['list-star', 'pagination']}))
        stars = [(li.find_next('a').attrs['href'], li.find_next('h3').text, urlparse(li.find_next('img').attrs['data-original']).path, li.find_next('ul').text.strip()) for li in doc.find('ul', {'class': 'list-star'}).find_all('li', recursive=False)]
        pages = [(urlparse(path).path + a.attrs['href'], a.text) for a in doc.find_all('a', text=['< Previous', 'Next >'])]
        return stars, pages

    @classmethod
    def most_popular_drama(cls, path):
        doc = BeautifulSoup(cls.get(path), 'html.parser', parse_only=SoupStrainer('ul', {'class': ['switch-block list-episode-item', 'pagination']}))
        shows = [a.attrs['href'] for a in doc.find_all('a', {'class': 'img'})]
        pages = [(urlparse(path).path + a.attrs['href'], a.text) for a in doc.find_all('a', text=['< Previous', 'Next >'])]
        return shows, pages

    @classmethod
    def recently_added(cls, path):
        doc = BeautifulSoup(cls.get(path), 'html.parser', parse_only=SoupStrainer('ul', {'class': ['switch-block list-episode-item', 'pagination']}))
        shows = [(a.attrs['href'], a.find('img').attrs['data-original'], '[COLOR orange]{}[/COLOR]'.format(a.find('h3').text) if a.find('span', {'class': 'type'}).text == 'RAW' else a.find('h3').text, int(a.find('span', {'class': 'ep'}).text.split()[1])) for a in doc.find_all('a', {'class': 'img'})]
        pages = [(urlparse(path).path + a.attrs['href'], a.text) for a in doc.find_all('a', text=['< Previous', 'Next >'])]
        return shows, pages

    @classmethod
    def search(cls, path):
        doc = BeautifulSoup(cls.get(path), 'html.parser', parse_only=SoupStrainer('ul', {'class': ['switch-block list-episode-item', 'pagination']}))
        shows = [(a.attrs['href'], a.find('h3').text, urlparse(a.find('img').attrs['data-original']).path) for a in doc.find_all('a', {'class': 'img'})]
        pages = [(urlparse(path).path + a.attrs['href'], a.text) for a in doc.find_all('a', text=['< Previous', 'Next >'])]
        return shows, pages

    @classmethod
    def star(cls, path):
        doc = BeautifulSoup(cls.get(path), 'html.parser', parse_only=SoupStrainer('ul', {'class': 'list-episode-item'}))
        return [a.attrs['href'] for a in doc.find_all('a')]

    @classmethod
    def video(cls, path):
        doc = BeautifulSoup(cls.get(path), 'html.parser', parse_only=SoupStrainer('div', {'class': 'block watch-drama'}))
        return doc.find('h1').text.strip(), doc.find('a').attrs['href'], [(urlparse(li.attrs['data-video'], 'https').geturl(), li.next.strip()) for li in doc.find_all('li', {'data-video': True})]

    @classmethod
    def episode_drama_detail(cls, path):
        doc = BeautifulSoup(cls.get(path), 'html.parser', parse_only=SoupStrainer('div', {'class': 'category'}))
        return cls.drama_detail(doc.find('a').attrs['href'])
