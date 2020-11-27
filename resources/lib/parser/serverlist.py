from parser import Parser


class ServerListParser(Parser):
    def __init__(self):
        super(ServerListParser, self).__init__()
        self._serverlist = []
        self._servertitlelist = []
        self._title = None
        self._is_title = False
        self._is_servertitle = False

    def close(self):
        return self._serverlist, self._servertitlelist, self._title

    def data(self, data):
        if self._is_servertitle:
            self._servertitlelist.append(data.strip())
            self._is_servertitle = False
        elif self._is_title:
            self._title = data.strip()
            self._is_title = False

    def end(self, tag):
        pass

    def start(self, tag, attrs):
        if tag == 'li' and 'data-video' in attrs:
            server = attrs['data-video']
            self._serverlist.append(server.replace('//', 'https://') if server.startswith('//') else server)
            self._is_servertitle = True
        elif tag == 'h1':
            self._is_title = True
