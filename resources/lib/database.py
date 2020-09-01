from xbmcaddon import Addon

import os
import sqlite3
import xbmc

__profile__ = xbmc.translatePath(Addon().getAddonInfo('profile'))

if not os.path.exists(__profile__):
    os.makedirs(__profile__)


class ExternalDatabase:
    _connection = None
    _cursor = None
    _database = os.path.join(__profile__, 'recently_viewed.db')

    @classmethod
    def add(cls, path):
        cls._cursor.execute('INSERT INTO recently_viewed (path) VALUES (?)', (path,))

    @classmethod
    def connect(cls):
        if cls._connection is None:
            cls._connection = sqlite3.connect(cls._database)
            cls._cursor = cls._connection.cursor()
            cls.create()

    @classmethod
    def close(cls):
        if cls._connection is None:
            return

        cls._connection.commit()
        cls._cursor.close()
        cls._connection.close()
        cls._connection = None

    @classmethod
    def create(cls):
        cls._cursor.execute('CREATE TABLE IF NOT EXISTS recently_viewed ('
                            'path TEXT PRIMARY KEY ON CONFLICT REPLACE, '
                            'last_visited DATETIME DEFAULT CURRENT_TIMESTAMP)')

    @classmethod
    def fetchall(cls):
        cls._cursor.execute('SELECT path FROM recently_viewed ORDER BY last_visited DESC')

        for (path,) in cls._cursor.fetchall():
            yield path

    @classmethod
    def remove(cls, path):
        cls._cursor.execute('DELETE FROM recently_viewed WHERE path = ?', (path,))


class InternalDatabase:
    _connection = None
    _cursor = None
    _database = os.path.join(xbmc.translatePath(Addon().getAddonInfo('path')), 'resources/data/drama.db')

    @classmethod
    def add(cls, values):
        cls._cursor.execute('INSERT INTO drama VALUES (?, ?, ?, ?, ?, ?, ?)', values)

    @classmethod
    def connect(cls):
        if cls._connection is None:
            cls._connection = sqlite3.connect(cls._database)
            cls._cursor = cls._connection.cursor()
            cls._cursor.row_factory = sqlite3.Row
            cls.create()

    @classmethod
    def close(cls):
        if cls._connection is None:
            return

        cls._connection.commit()
        cls._cursor.close()
        cls._connection.close()
        cls._connection = None

    @classmethod
    def create(cls):
        cls._cursor.execute('CREATE TABLE IF NOT EXISTS drama ('
                            'path TEXT PRIMARY KEY ON CONFLICT IGNORE, '
                            'poster TEXT, '
                            'title TEXT, '
                            'plot TEXT, '
                            'country TEXT, '
                            'status TEXT, '
                            'year SMALLINT)')

    @classmethod
    def fetchone(cls, path):
        cls._cursor.execute('SELECT * FROM drama WHERE path = ?', (path,))
        result = cls._cursor.fetchone()

        if result is None:
            return None
        else:
            result = dict(result)
            result.pop('path')
            return result
