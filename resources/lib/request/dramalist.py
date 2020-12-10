from request import Parser


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
    def __init__(self, selectvalue):
        super(CharDramaListParser, self).__init__()
        self._dramalist = []
        self._selectvalue = selectvalue
        self._is_selectvalue = False
        self._validate_selectvalue = False

    def close(self):
        return self._dramalist

    def data(self, data):
        if self._validate_selectvalue:
            self._is_selectvalue = self._selectvalue == data
            self._validate_selectvalue = False

    def end(self, tag):
        if tag == 'ul':
            self._is_selectvalue = False

    def start(self, tag, attrs):
        if self._is_selectvalue and tag == 'a':
            self._dramalist.append(attrs['href'])
        elif not attrs and tag == 'h4':
            self._is_selectvalue = True
            self._validate_selectvalue = True


class GenreDramaListParser(Parser):
    def __init__(self, selectvalue):
        super(GenreDramaListParser, self).__init__()
        self._dramalist = []
        self._selectvalue = selectvalue
        self._is_selectvalue = False

    def close(self):
        return self._dramalist

    def data(self, data):
        pass

    def end(self, tag):
        pass

    def start(self, tag, attrs):
        if self._is_selectvalue and tag == 'a':
            self._dramalist.append(attrs['href'])
            self._is_selectvalue = False
        elif tag == 'li' and 'data-genre' in attrs and self._selectvalue in attrs['data-genre']:
            self._is_selectvalue = True


class StatusYearDramaListParser(Parser):
    def __init__(self, selectid, selectvalue):
        super(StatusYearDramaListParser, self).__init__()
        self._dramalist = []
        self._selectvalue = f'{selectid}_{selectvalue}'
        self._is_selectvalue = False

    def close(self):
        return self._dramalist

    def data(self, data):
        pass

    def end(self, tag):
        pass

    def start(self, tag, attrs):
        if self._is_selectvalue and tag == 'a':
            self._dramalist.append(attrs['href'])
            self._is_selectvalue = False
        elif tag == 'li' and 'class' in attrs and self._selectvalue in attrs['class']:
            self._is_selectvalue = True
