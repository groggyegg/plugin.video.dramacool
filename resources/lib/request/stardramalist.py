from request import Parser


class StarDramaListParser(Parser):
    def __init__(self):
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
