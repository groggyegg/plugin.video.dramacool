import os
import request
import sqlite3
import xbmcaddon
import xbmcvfs

_SQLITE_MAX_VARIABLE_NUMBER = 999
_connection = None
_database = os.path.join(xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path')), 'resources/data/drama.db')


def connect():
    global _connection

    if _connection is None:
        _connection = sqlite3.connect(_database)


def close():
    global _connection

    if _connection is not None:
        _connection.commit()
        _connection.close()
        _connection = None


def create():
    _connection.execute('CREATE TABLE IF NOT EXISTS drama ('
                        'path TEXT PRIMARY KEY ON CONFLICT IGNORE, '
                        'poster TEXT, '
                        'title TEXT, '
                        'plot TEXT, '
                        'year INT)')

    cursor = _connection.execute('SELECT path FROM drama')
    result = {path for (path,) in cursor.fetchall()}

    for path in request.parse('/drama-list', 'DramaListParser'):
        if path not in result:
            add(path)


def add(path):
    (poster, title, plot, year) = request.parse(path, 'DramaDetailParser')
    _connection.execute('INSERT INTO drama VALUES (?, ?, ?, ?, ?)', (path, poster, title, plot, year))
    return poster, {'title': title, 'plot': plot, 'year': year}


def fetchone(path):
    cursor = _connection.execute('SELECT poster, title, plot, year FROM drama WHERE path = ?', (path,))
    result = cursor.fetchone()

    if result is None:
        return add(path)
    else:
        (poster, title, plot, year) = result
        return poster, {'title': title, 'plot': plot, 'year': year}


def fetchplot(poster):
    cursor = _connection.execute('SELECT title, plot, year FROM drama WHERE poster = ?', (poster,))
    result = cursor.fetchone()

    if result is None:
        return {}
    else:
        (title, plot, year) = result
        return {'title': title, 'plot': plot, 'year': year}


def fetchall(pathlist):
    pathset = set(pathlist)

    for i in range(0, len(pathlist), _SQLITE_MAX_VARIABLE_NUMBER):
        pathchunk = pathlist[i:i + _SQLITE_MAX_VARIABLE_NUMBER]
        cursor = _connection.execute('SELECT * FROM drama WHERE path IN (%s)' % ', '.join('?' * len(pathchunk)), pathchunk)

        for (path, poster, title, plot, year) in cursor.fetchall():
            pathset.discard(path)
            yield path, poster, {'title': title, 'plot': plot, 'year': year}

    for path in pathset:
        (poster, info) = add(path)
        yield path, poster, info
