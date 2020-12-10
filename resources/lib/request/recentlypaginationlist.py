from request import Parser


class RecentlyPaginationListParser(Parser):
    def __init__(self):
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
            self._recentlylist.append((self._path, self._poster, f'[{self._type}] {self._title} {data}'))
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
