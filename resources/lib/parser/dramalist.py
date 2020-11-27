from parser import Parser


class DramaListParser(Parser):
    def __init__(self):
        super(DramaListParser, self).__init__()
        self._dramalist = []
        self._is_item = False

    def close(self):
        return self._dramalist

    def data(self, data):
        pass

    def end(self, tag):
        pass

    def start(self, tag, attrs):
        if self._is_item and tag == 'a':
            self._dramalist.append(attrs['href'])
            self._is_item = False
        elif tag == 'li' and 'data-genre' in attrs:
            self._is_item = True


class CharDramaListParser(Parser):
    def __init__(self, filterchar):
        super(CharDramaListParser, self).__init__()
        self._dramalist = []
        self._filterchar = filterchar
        self._is_char = False
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
        elif not attrs and tag == 'h4':
            self._is_char = True
            self._validate_char = True


class GenreDramaListParser(Parser):
    def __init__(self, filtergenre):
        super(GenreDramaListParser, self).__init__()
        self._dramalist = []
        self._filtergenre = filtergenre
        self._is_genre = False

    def close(self):
        return self._dramalist

    def data(self, data):
        pass

    def end(self, tag):
        pass

    def start(self, tag, attrs):
        if self._is_genre and tag == 'a':
            self._dramalist.append(attrs['href'])
            self._is_genre = False
        elif tag == 'li' and 'data-genre' in attrs and self._filtergenre in attrs['data-genre']:
            self._is_genre = True


class StatusDramaListParser(Parser):
    def __init__(self, filterstatus):
        super(StatusDramaListParser, self).__init__()
        self._dramalist = []
        self._filterstatus = f'status_{filterstatus}'
        self._is_status = False

    def close(self):
        return self._dramalist

    def data(self, data):
        pass

    def end(self, tag):
        pass

    def start(self, tag, attrs):
        if self._is_status and tag == 'a':
            self._dramalist.append(attrs['href'])
            self._is_status = False
        elif tag == 'li' and 'class' in attrs and self._filterstatus in attrs['class']:
            self._is_status = True


class YearDramaListParser(Parser):
    def __init__(self, filteryear):
        super(YearDramaListParser, self).__init__()
        self._dramalist = []
        self._filteryear = f'year_{filteryear}'
        self._is_year = False

    def close(self):
        return self._dramalist

    def data(self, data):
        pass

    def end(self, tag):
        pass

    def start(self, tag, attrs):
        if self._is_year and tag == 'a':
            self._dramalist.append(attrs['href'])
            self._is_year = False
        elif tag == 'li' and 'class' in attrs and self._filteryear in attrs['class']:
            self._is_year = True
