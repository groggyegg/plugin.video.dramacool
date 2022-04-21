"""
MIT License

Copyright (c) 2020 groggyegg

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from json import loads, dumps
from os import makedirs, remove
from os.path import exists, join

from peewee import CharField, Model, SmallIntegerField, SQL, SqliteDatabase, TextField
from playhouse.sqlite_ext import DateTimeField
from xbmcext import ListItem, getPath, getProfilePath

__all__ = ['Drama', 'ExternalDatabase', 'InternalDatabase', 'RecentDrama', 'RecentFilter']


class JSONField(CharField):
    def db_value(self, value):
        if isinstance(value, str):
            return value
        else:
            return dumps(value)

    def python_value(self, value):
        return loads(value)


class ExternalDatabase(object):
    profile = getProfilePath()
    connection = SqliteDatabase(join(profile, 'dramacool.db'))

    @staticmethod
    def close():
        ExternalDatabase.connection.close()

    @staticmethod
    def connect():
        if not exists(ExternalDatabase.profile):
            makedirs(ExternalDatabase.profile)

        ExternalDatabase.connection.connect(True)

    @staticmethod
    def create():
        ExternalDatabase.connection.create_tables([RecentDrama, RecentFilter])
        ExternalDatabase.migration_20211114()
        ExternalDatabase.connection.commit()

    @staticmethod
    def migration_20211114():
        connection = SqliteDatabase(join(ExternalDatabase.profile, 'recently_viewed.db'))

        if exists(connection.database):
            class RecentlyViewed(Model):
                path = TextField(primary_key=True, constraints=[SQL('ON CONFLICT REPLACE')])
                last_visited = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

                class Meta:
                    database = connection
                    table_name = 'recently_viewed'

            for recently_viewed in RecentlyViewed.select():
                RecentDrama.create(path=recently_viewed.path, timestamp=recently_viewed.last_visited)

            connection.close()
            remove(connection.database)


class InternalDatabase(object):
    connection = SqliteDatabase(join(getPath(), 'resources/data/dramacool.db'))

    @staticmethod
    def close():
        InternalDatabase.connection.close()

    @staticmethod
    def connect():
        InternalDatabase.connection.connect(True)

    @staticmethod
    def create():
        from request import DramaDetailRequest, DramaListRequest

        InternalDatabase.connection.create_tables([Drama])

        paths = {drama.path for drama in Drama.select().where((Drama.status == 'Completed') & Drama.mediatype.is_null(False))}
        mediatypes = ['/category/korean-movies', '/category/japanese-movies', '/category/taiwanese-movies', '/category/hong-kong-movies',
                      '/category/chinese-movies', '/category/american-movies', '/category/other-asia-movies', '/category/thailand-movies',
                      '/category/indian-movies', '/category/korean-drama', '/category/japanese-drama', '/category/taiwanese-drama',
                      '/category/hong-kong-drama', '/category/chinese-drama', '/category/american-drama', '/category/other-asia-drama',
                      '/category/thailand-drama', '/category/indian-drama', '/kshow']

        for mediatype in mediatypes:
            for path in DramaListRequest().get(mediatype):
                if path not in paths:
                    Drama.create(mediatype=mediatype, **DramaDetailRequest().get(path))

        InternalDatabase.connection.commit()


class ExternalModel(Model):
    class Meta:
        database = ExternalDatabase.connection


class InternalModel(Model):
    class Meta:
        database = InternalDatabase.connection


class Drama(InternalModel, ListItem):
    path = CharField(primary_key=True, constraints=[SQL('ON CONFLICT REPLACE')])
    poster = CharField(null=True)
    title = CharField(index=True)
    plot = CharField(null=True)
    country = CharField(null=True, index=True)
    status = CharField(null=True, index=True)
    genre = JSONField(null=True, index=True)
    year = SmallIntegerField(null=True, index=True)
    mediatype = CharField(null=True, index=True)

    def __new__(cls, *args, **kwargs):
        return super(Drama, cls).__new__(cls)

    def __init__(self, *args, **kwargs):
        super(Drama, self).__init__(*args, **kwargs)
        self.setLabel(kwargs.pop('title'))
        self.setArt({'icon': kwargs['poster'], 'poster': kwargs['poster']} if 'poster' in kwargs else {})
        self.setInfo('video', {'title': kwargs.pop('title') if 'title' in kwargs else None,
                               'plot': kwargs.pop('plot') if 'plot' in kwargs else None,
                               'country': kwargs.pop('country') if 'country' in kwargs else None,
                               'status': kwargs.pop('status') if 'status' in kwargs else None,
                               'genre': kwargs.pop('genre') if 'genre' in kwargs else None,
                               'year': kwargs.pop('year') if 'year' in kwargs else None})


class RecentDrama(ExternalModel):
    path = CharField(primary_key=True, constraints=[SQL('ON CONFLICT REPLACE')])
    timestamp = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])


class RecentFilter(ExternalModel, ListItem):
    path = CharField(null=False)
    title = CharField(primary_key=True, constraints=[SQL('ON CONFLICT REPLACE')])
    timestamp = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

    def __new__(cls, *args, **kwargs):
        return super(RecentFilter, cls).__new__(cls)

    def __init__(self, *args, **kwargs):
        super(RecentFilter, self).__init__(*args, **kwargs)
        self.setLabel(kwargs.pop('title'))
        self.setArt({'icon': 'DefaultTVShows.png'})
