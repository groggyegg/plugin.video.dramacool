from request import Parser

import json


class DramaListParser(Parser):
    def __init__(self):
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


class CharGenreStatusYearDramaListParser(Parser):
    def __init__(self, chars, years, genres, statuses):
        self._decode_class = False
        self._decode_datagenre = False
        self._parsers = []

        if chars:
            self._parsers.append(CharDramaListParser(chars))

        if genres:
            self._decode_datagenre = True
            self._parsers.append(GenreDramaListParser(genres))

        if statuses:
            self._decode_class = True
            self._parsers.append(StatusYearDramaListParser('status', statuses))

        if years:
            self._parsers.append(StatusYearDramaListParser('year', years))

        if not chars and not years and not genres and not statuses:
            self._parsers.append(DramaListParser())

    def close(self):
        result = set(self._parsers.pop().close())

        for parser in self._parsers:
            result.intersection_update(parser.close())

        return list(result)

    def data(self, data):
        for parser in self._parsers:
            parser.data(data)

    def end(self, tag):
        for parser in self._parsers:
            parser.end(tag)

    def start(self, tag, attrs):
        if self._decode_datagenre and 'data-genre' in attrs:
            attrs['data-genre'] = set(json.loads(attrs['data-genre']))

        if self._decode_class and 'class' in attrs:
            attrs['class'] = set(attrs['class'].split())

        for parser in self._parsers:
            parser.start(tag, attrs)


class CharDramaListParser:
    def __init__(self, selectvalues):
        self._dramalist = set()
        self._selectvalues = set(selectvalues)
        self._is_selectvalue = False
        self._validate_selectvalue = False

    def close(self):
        return self._dramalist

    def data(self, data):
        if self._validate_selectvalue:
            self._is_selectvalue = data in self._selectvalues
            self._validate_selectvalue = False

    def end(self, tag):
        if tag == 'ul':
            self._is_selectvalue = False

    def start(self, tag, attrs):
        if self._is_selectvalue and tag == 'a':
            self._dramalist.add(attrs['href'])
        elif not attrs and tag == 'h4':
            self._is_selectvalue = True
            self._validate_selectvalue = True


class GenreDramaListParser:
    def __init__(self, selectvalues):
        self._dramalist = set()
        self._selectvalues = set(selectvalues)
        self._is_selectvalue = False

    def close(self):
        return self._dramalist

    def data(self, data):
        pass

    def end(self, tag):
        pass

    def start(self, tag, attrs):
        if self._is_selectvalue and tag == 'a':
            self._dramalist.add(attrs['href'])
            self._is_selectvalue = False
        elif tag == 'li' and 'data-genre' in attrs and self._selectvalues.issubset(attrs['data-genre']):
            self._is_selectvalue = True


class StatusYearDramaListParser:
    def __init__(self, selectid, selectvalues):
        self._dramalist = set()
        self._selectvalues = {f'{selectid}_{selectvalue}' for selectvalue in selectvalues}
        self._is_selectvalue = False

    def close(self):
        return self._dramalist

    def data(self, data):
        pass

    def end(self, tag):
        pass

    def start(self, tag, attrs):
        if self._is_selectvalue and tag == 'a':
            self._dramalist.add(attrs['href'])
            self._is_selectvalue = False
        elif tag == 'li' and 'class' in attrs and not self._selectvalues.isdisjoint(attrs['class']):
            self._is_selectvalue = True
