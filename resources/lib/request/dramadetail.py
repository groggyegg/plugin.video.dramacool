from database import Drama
from request import Parser


class DramaDetailParser(Parser):
    def __init__(self, path_):
        self._path = path_
        self._poster = None
        self._title = None
        self._plot = []
        self._country = None
        self._genre = []
        self._year = None
        self._is_span = False
        self._is_poster = False
        self._is_title = False
        self._is_plot = False
        self._is_country = False
        self._is_genre = False
        self._is_genre_a = False
        self._is_year = False

    def close(self):
        return Drama.create(path=self._path, poster=self._poster, title=self._title, plot=' '.join(self._plot), country=self._country, genre=self._genre, year=self._year)

    def data(self, data):
        if self._is_span:
            self._is_plot = True if 'Description' in data else False
            self._is_country = True if 'Country' in data else False
            self._is_genre = True if 'Genre' in data else False
            self._is_year = True if 'Released' in data else False
        elif self._is_title:
            self._title = data.strip()
            self._is_title = False
        elif self._is_plot:
            data = data.strip()

            if data:
                self._plot.append(data.replace('\r\n\r\n', '\r\n'))
        elif self._is_country:
            self._country = data
        elif self._is_genre and self._is_genre_a:
            self._genre.append(data)
            self._is_genre_a = False
        elif self._is_year and data.isdigit():
            self._year = int(data)

    def end(self, tag):
        if tag == 'p':
            self._is_country = False
            self._is_genre = False
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
        elif self._is_genre and tag == 'a':
            self._is_genre_a = True
