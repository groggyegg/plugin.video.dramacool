from request import Parser


class EpisodeListParser(Parser):
    def __init__(self):
        self._episodelist = []
        self._path = None
        self._type = None
        self._is_ul = False
        self._is_title = False
        self._is_type = False

    def close(self):
        return reversed(self._episodelist)

    def data(self, data):
        if self._is_type:
            self._type = data
            self._is_type = False
        elif self._is_title:
            self._episodelist.append((self._path, f'[{self._type}] {data.strip()}'))
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
