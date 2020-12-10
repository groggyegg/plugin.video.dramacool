from request import Parser


class DramaPaginationListParser(Parser):
    def __init__(self):
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
