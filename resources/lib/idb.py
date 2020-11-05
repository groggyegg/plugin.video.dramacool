import os
import request
import sqlite3

try:
    import xbmc
    import xbmcaddon

    _database = os.path.join(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')), 'resources/data/drama.db')
except ImportError:
    _database = '../data/drama.db'

_connection = None


def connect():
    global _connection

    if _connection is None:
        _connection = sqlite3.connect(_database)
        _connection.row_factory = sqlite3.Row


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

    for path in request.dramalist('/drama-list'):
        if path not in result:
            add(path)


def add(path):
    (poster, title, plot, year) = request.dramadetail(path)
    _connection.execute('INSERT INTO drama VALUES (?, ?, ?, ?, ?)', (path, poster, title, plot, year))
    return poster, {'title': title, 'plot': plot, 'year': year}


def fetchone(path):
    cursor = _connection.execute('SELECT poster, title, plot, year FROM drama WHERE path = ?', (path,))
    result = cursor.fetchone()

    if result is None:
        return add(path)
    else:
        result = dict(result)
        return result.pop('poster'), result


def fetchmany(paths):
    cursor = _connection.execute('SELECT * FROM drama WHERE path IN (%s)' % ', '.join('?' * len(paths)), paths)
    paths = set(paths)

    for result in cursor.fetchall():
        result = dict(result)
        paths.discard(result.pop('path'))
        yield result.pop('poster'), result

    for path in paths:
        yield add(path)
