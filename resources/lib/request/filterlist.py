from request import Parser


class FilterListParser(Parser):
    def __init__(self):
        self._parsers = [CharFilterListParser(), StatusYearFilterListParser('status'), StatusYearFilterListParser('year')]

    def close(self):
        return [parser.close() for parser in self._parsers]

    def data(self, data):
        for parser in self._parsers:
            parser.data(data)

    def end(self, tag):
        for parser in self._parsers:
            parser.end(tag)

    def start(self, tag, attrs):
        for parser in self._parsers:
            parser.start(tag, attrs)


class CharFilterListParser:
    def __init__(self):
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


class StatusYearFilterListParser:
    def __init__(self, selectid):
        self._filterlist = []
        self._selectid = f'select-{selectid}'
        self._is_selectid = False

    def close(self):
        return self._filterlist

    def data(self, data):
        pass

    def end(self, tag):
        if tag == 'select':
            self._is_selectid = False

    def start(self, tag, attrs):
        if self._is_selectid and tag == 'option' and attrs['value']:
            self._filterlist.append(attrs['value'])
        elif tag == 'select' and 'id' in attrs and self._selectid in attrs['id']:
            self._is_selectid = True
