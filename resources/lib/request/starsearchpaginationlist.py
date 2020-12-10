from request import Parser


class StarSearchPaginationListParser(Parser):
    def __init__(self):
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
