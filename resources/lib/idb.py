import os
import sqlite3
import xbmc
import xbmcaddon

_connection = None
_database = os.path.join(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')), 'resources/data/drama.db')


def add(values):
    _connection.execute('INSERT INTO drama VALUES (?, ?, ?, ?, ?)', values)


def connect():
    global _connection

    if _connection is None:
        _connection = sqlite3.connect(_database)
        _connection.row_factory = sqlite3.Row
        create()


def close():
    global _connection

    if _connection is not None:
        _connection.commit()
        _connection.close()
        _connection = None


def create():
    _connection.execute('CREATE TABLE IF NOT EXISTS drama ('
                        'path TEXT UNIQUE ON CONFLICT IGNORE, '
                        'poster TEXT, '
                        'title TEXT, '
                        'plot TEXT, '
                        'year INT)')


def fetchone(path):
    cursor = _connection.execute('SELECT * FROM drama WHERE path = ?', (path,))
    result = cursor.fetchone()

    if result is None:
        return None
    else:
        result = dict(result)
        result.pop('path')
        return result
