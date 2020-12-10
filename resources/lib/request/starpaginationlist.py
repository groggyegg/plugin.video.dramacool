from request import Parser


class StarPaginationListParser(Parser):
    def __init__(self):
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
