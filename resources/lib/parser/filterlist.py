from parser import Parser


class CharFilterListParser(Parser):
    def __init__(self):
        super(CharFilterListParser, self).__init__()
        self._filterlist = []
        self._is_char = False

    def close(self):
        return self._filterlist

    def data(self, data):
        if self._is_char:
            self._filterlist.append(data)
            self._is_char = False

    def end(self, tag):
        pass

    def start(self, tag, attrs):
        if not attrs and tag == 'h4':
            self._is_char = True


class StatusFilterListParser(Parser):
    def __init__(self):
        super(StatusFilterListParser, self).__init__()
        self._filterlist = []
        self._is_status = False

    def close(self):
        return self._filterlist

    def data(self, data):
        pass

    def end(self, tag):
        if tag == 'select':
            self._is_status = False

    def start(self, tag, attrs):
        if self._is_status and tag == 'option' and attrs['value']:
            self._filterlist.append(attrs['value'])
        elif tag == 'select' and 'id' in attrs and 'select-status' in attrs['id']:
            self._is_status = True


class YearFilterListParser(Parser):
    def __init__(self):
        super(YearFilterListParser, self).__init__()
        self._filterlist = []
        self._is_year = False

    def close(self):
        return self._filterlist

    def data(self, data):
        pass

    def end(self, tag):
        if tag == 'select':
            self._is_year = False

    def start(self, tag, attrs):
        if self._is_year and tag == 'option' and attrs['value']:
            self._filterlist.append(attrs['value'])
        elif tag == 'select' and 'id' in attrs and 'select-year' in attrs['id']:
            self._is_year = True
