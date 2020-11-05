import os
import re

import requests

try:
    import xbmc
    import xbmcaddon

    _tempfile = os.path.join(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')), 'resources/data/tempfile')
except ImportError:
    pass

try:
    import lxml.etree

    Parser = object


    def parse(text, target):
        return lxml.etree.HTML(text, lxml.etree.HTMLParser(target=target))
except ImportError:
    import HTMLParser


    class Parser(HTMLParser.HTMLParser):
        def error(self, message):
            pass

        def handle_data(self, data):
            self.data(data)

        def handle_endtag(self, tag):
            self.end(tag)

        def handle_starttag(self, tag, attrs):
            self.start(tag, dict(attrs))


    def parse(text, target):
        target.feed(text)
        return target.close()

_domains = ('https://watchasian.net', 'https://dramacool.so')
_session = requests.Session()


class _DramaDetailParser(Parser):
    def __init__(self):
        Parser.__init__(self)
        self._poster = None
        self._title = None
        self._plot = []
        self._year = None
        self._is_span = False
        self._is_poster = False
        self._is_title = False
        self._is_plot = False
        self._is_year = False

    def close(self):
        return self._poster, self._title, ' '.join(self._plot), self._year

    def data(self, data):
        if self._is_span:
            self._is_plot = True if 'Description' in data else False
            self._is_year = True if 'Released' in data else False
        elif self._is_title:
            self._title = data.strip()
            self._is_title = False
        elif self._is_plot:
            data = data.strip()

            if data:
                self._plot.append(data.replace('\r\n\r\n', '\r\n'))
        elif self._is_year and data.isdigit():
            self._year = int(data)

    def end(self, tag):
        if tag == 'p':
            self._is_year = False

        self._is_span = False

    def start(self, tag, attrs):
        if tag == 'span':
            self._is_span = True
        elif tag == 'h1':
            self._is_title = True
        elif self._is_poster:
            self._poster = attrs['src']
            self._is_poster = False
        elif tag == 'div' and 'class' in attrs and 'img' in attrs['class']:
            self._is_poster = True


class _DramaListParser(Parser):
    def __init__(self, filterchar, filteryear, filterstatus):
        Parser.__init__(self)
        self._dramalist = []
        self._filterchar = filterchar
        self._filteryear = filteryear
        self._filterstatus = filterstatus
        self._filternone = filterchar == '' and filteryear == '' and filterstatus == ''
        self._is_char = False
        self._is_year = False
        self._is_status = False
        self._is_none = False
        self._validate_char = False

    def close(self):
        return self._dramalist

    def data(self, data):
        if self._validate_char:
            self._is_char = self._filterchar == data
            self._validate_char = False

    def end(self, tag):
        if tag == 'ul':
            self._is_char = False

    def start(self, tag, attrs):
        if self._is_char and tag == 'a':
            self._dramalist.append(attrs['href'])
        elif self._filterchar and not attrs and tag == 'h4':
            self._is_char = True
            self._validate_char = True
        elif self._is_status and tag == 'a':
            self._dramalist.append(attrs['href'])
            self._is_status = False
        elif self._filterstatus and tag == 'li' and 'class' in attrs and self._filterstatus in attrs['class']:
            self._is_status = True
        elif self._is_year and tag == 'a':
            self._dramalist.append(attrs['href'])
            self._is_year = False
        elif self._filteryear and tag == 'li' and 'class' in attrs and self._filteryear in attrs['class']:
            self._is_year = True
        elif self._is_none and tag == 'a':
            self._dramalist.append(attrs['href'])
            self._is_none = False
        elif self._filternone and tag == 'li' and 'data-genre' in attrs:
            self._is_none = True


class _DramaPaginationListParser(Parser):
    def __init__(self):
        Parser.__init__(self)
        self._dramalist = []
        self._paginationlist = []
        self._title = None
        self._is_list = False
        self._is_pagination = False

    def close(self):
        return self._dramalist, self._paginationlist

    def data(self, data):
        pass

    def end(self, tag):
        if tag == 'ul':
            self._is_list = False

    def start(self, tag, attrs):
        if self._is_list and tag == 'a':
            self._dramalist.append(attrs['href'])
        elif self._is_pagination:
            self._paginationlist.append((attrs['href'], self._title))
            self._is_pagination = False
        elif tag == 'ul' and 'class' in attrs and 'list-episode-item' in attrs['class']:
            self._is_list = True
        elif tag == 'li' and 'class' in attrs and ('next' in attrs['class'] or 'previous' in attrs['class']):
            self._title = attrs['class']
            self._is_pagination = True


class _EpisodeListParser(Parser):
    def __init__(self):
        Parser.__init__(self)
        self._episodelist = []
        self._path = None
        self._type = None
        self._is_ul = False
        self._is_title = False
        self._is_type = False

    def close(self):
        return self._episodelist

    def data(self, data):
        if self._is_type:
            self._type = data
            self._is_type = False
        elif self._is_title:
            self._episodelist.append((self._path, u'[{}] {}'.format(self._type, data.strip())))
            self._is_title = False

    def end(self, tag):
        if self._is_ul and tag == 'ul':
            self._is_ul = False

    def start(self, tag, attrs):
        if self._is_ul:
            if tag == 'a':
                self._path = attrs['href']
            elif tag == 'span' and 'type' in attrs['class']:
                self._is_type = True
            elif tag == 'h3':
                self._is_title = True
        elif tag == 'ul' and 'class' in attrs and 'all-episode' in attrs['class']:
            self._is_ul = True


class _FilterListParser(Parser):
    def __init__(self, listchar, listyear, liststatus):
        Parser.__init__(self)
        self._filterlist = []
        self._listchar = listchar
        self._listyear = listyear
        self._liststatus = liststatus
        self._is_char = False
        self._is_year = False
        self._is_status = False

    def close(self):
        return self._filterlist

    def data(self, data):
        if self._is_char:
            self._filterlist.append(data)
            self._is_char = False

    def end(self, tag):
        if tag == 'select':
            self._is_status = False
            self._is_year = False

    def start(self, tag, attrs):
        if self._listchar and not attrs and tag == 'h4':
            self._is_char = True
        elif self._is_status and tag == 'option' and attrs['value']:
            self._filterlist.append(attrs['value'])
        elif self._liststatus and tag == 'select' and 'id' in attrs and 'select-status' in attrs['id']:
            self._is_status = True
        elif self._is_year and tag == 'option' and attrs['value']:
            self._filterlist.append(attrs['value'])
        elif self._listyear and tag == 'select' and 'id' in attrs and 'select-year' in attrs['id']:
            self._is_year = True


class _RecentlyPaginationListParser(Parser):
    def __init__(self):
        Parser.__init__(self)
        self._recentlylist = []
        self._paginationlist = []
        self._path = None
        self._poster = None
        self._title = None
        self._type = None
        self._is_list = False
        self._is_pagination = False
        self._is_title = False
        self._is_type = False
        self._is_ep = False

    def close(self):
        return self._recentlylist, self._paginationlist

    def data(self, data):
        if self._is_type:
            self._type = data
            self._is_type = False
        elif self._is_title:
            self._title = data
            self._is_title = False
        elif self._is_ep:
            self._recentlylist.append((self._path, self._poster, u'[{}] {} {}'.format(self._type, self._title, data)))
            self._is_ep = False

    def end(self, tag):
        if self._is_list and tag == 'ul':
            self._is_list = False

    def start(self, tag, attrs):
        if self._is_list:
            if tag == 'a':
                self._path = attrs['href']
            elif tag == 'img':
                self._poster = attrs['data-original']
            elif tag == 'span':
                if 'type' in attrs['class']:
                    self._is_type = True
                elif 'ep' in attrs['class']:
                    self._is_ep = True
            elif tag == 'h3':
                self._is_title = True
        elif self._is_pagination:
            self._paginationlist.append((attrs['href'], self._title))
            self._is_pagination = False
        elif tag == 'ul' and 'class' in attrs and 'list-episode-item' in attrs['class']:
            self._is_list = True
        elif tag == 'li' and 'class' in attrs and ('next' in attrs['class'] or 'previous' in attrs['class']):
            self._title = attrs['class']
            self._is_pagination = True


class _ServerListParser(Parser):
    def __init__(self):
        Parser.__init__(self)
        self._serverlist = []
        self._servertitlelist = []
        self._title = None
        self._is_title = False
        self._is_servertitle = False

    def close(self):
        return self._serverlist, self._servertitlelist, self._title

    def data(self, data):
        if self._is_servertitle:
            self._servertitlelist.append(data.strip())
            self._is_servertitle = False
        elif self._is_title:
            self._title = data.strip()
            self._is_title = False

    def end(self, tag):
        pass

    def start(self, tag, attrs):
        if tag == 'li' and 'data-video' in attrs:
            server = attrs['data-video']
            self._serverlist.append(server.replace('//', 'https://') if server.startswith('//') else server)
            self._is_servertitle = True
        elif tag == 'h1':
            self._is_title = True


class _StarDramaListParser(Parser):
    def __init__(self):
        Parser.__init__(self)
        self._dramalist = []

    def close(self):
        return self._dramalist

    def data(self, data):
        pass

    def end(self, tag):
        pass

    def start(self, tag, attrs):
        if tag == 'a' and 'class' in attrs and 'img' in attrs['class']:
            self._dramalist.append(attrs['href'])


class _StarPaginationListParser(Parser):
    def __init__(self):
        Parser.__init__(self)
        self._starlist = []
        self._paginationlist = []
        self._path = None
        self._poster = None
        self._title = None
        self._plot = None
        self._is_star = False
        self._is_pagination = False
        self._is_title = False
        self._is_plot = False

    def close(self):
        return self._starlist, self._paginationlist

    def data(self, data):
        if self._is_title:
            self._title = data
            self._is_title = False
        elif self._is_plot:
            self._plot.append(data)

    def end(self, tag):
        if self._is_star and tag == 'ul':
            self._is_star = False
            self._is_plot = False
            self._starlist.append((
                self._path, self._poster, self._title, ''.join(self._plot).strip().replace('\t', '')))

    def start(self, tag, attrs):
        if self._is_star:
            if tag == 'ul':
                self._plot = []
                self._is_plot = True
            elif tag == 'a':
                self._path = attrs['href']
                self._is_title = True
        elif self._is_pagination:
            self._paginationlist.append((attrs['href'], self._title))
            self._is_pagination = False
        elif tag == 'img' and 'class' in attrs:
            self._poster = attrs['data-original']
            self._is_star = True
        elif tag == 'li' and 'class' in attrs and ('next' in attrs['class'] or 'previous' in attrs['class']):
            self._title = attrs['class']
            self._is_pagination = True


class _StarSearchPaginationListParser(Parser):
    def __init__(self):
        Parser.__init__(self)
        self._starlist = []
        self._paginationlist = []
        self._path = None
        self._title = None
        self._is_list = False
        self._is_pagination = False

    def close(self):
        return self._starlist, self._paginationlist

    def data(self, data):
        pass

    def end(self, tag):
        if self._is_list and tag == 'ul':
            self._is_list = False

    def start(self, tag, attrs):
        if self._is_list:
            if tag == 'a':
                self._path = attrs['href']
            elif tag == 'img':
                self._starlist.append((self._path, attrs['data-original'], attrs['alt']))
        elif self._is_pagination:
            self._is_pagination = False
            self._paginationlist.append((attrs['href'], self._title))
        elif tag == 'ul' and 'class' in attrs and 'list-episode-item' in attrs['class']:
            self._is_list = True
        elif tag == 'li' and 'class' in attrs and ('next' in attrs['class'] or 'previous' in attrs['class']):
            self._title = attrs['class']
            self._is_pagination = True


def dramadetail(path):
    return parse(get(path).text, _DramaDetailParser())


def dramalist(path, filterchar='', filteryear='', filterstatus=''):
    return parse(get(path).text, _DramaListParser(filterchar, filteryear, filterstatus))


def dramapaginationlist(path):
    return parse(get(path).text, _DramaPaginationListParser())


def episodelist(path):
    return parse(get(path).text, _EpisodeListParser())


def filterlist(path, listchar=False, listyear=False, liststatus=False):
    return parse(get(path).text, _FilterListParser(listchar, listyear, liststatus))


def recentlypaginationlist(path):
    return parse(get(path).text, _RecentlyPaginationListParser())


def serverlist(path):
    return parse(get(path).text, _ServerListParser())


def stardramalist(path):
    return parse(get(path).text, _StarDramaListParser())


def starpaginationlist(path):
    return parse(get(path).text, _StarPaginationListParser())


def starsearchpaginationlist(path):
    return parse(get(path).text, _StarSearchPaginationListParser())


def subtitle(url):
    match = re.search('&sub=([^&]+)', url)

    if match:
        webvtt = get('/player/sub/index.php?id=' + match.group(1), 'https://embed.watchasian.to').content.replace(
            '\xef\xbb\xbfWEBVTT\r\n\r\n', '', 1).split('\r\n\r\n')

        with open(_tempfile, 'w') as o:
            for counter, text in enumerate(webvtt, start=1):
                o.write(str(counter) + '\r\n' + text + '\r\n\r\n')

            return _tempfile

    return None


def get(pathquery, domain=''):
    if domain:
        response = _session.get(domain + pathquery)

        if response.status_code == 200:
            return response
    else:
        for domain in _domains:
            response = _session.get(domain + pathquery)

            if response.status_code == 200:
                return response
