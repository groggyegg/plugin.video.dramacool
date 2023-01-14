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

from json import dumps, loads
from os import makedirs, path

from peewee import CharField, Model, SmallIntegerField, SQL, SqliteDatabase
from playhouse.sqlite_ext import DateTimeField
from xbmcext import ListItem, getAddonPath, getAddonProfilePath


class JSONField(CharField):
    def db_value(self, value):
        if isinstance(value, str):
            return value
        else:
            return dumps(value)

    def python_value(self, value):
        return loads(value)


class ExternalDatabase(object):
    connection = None

    @classmethod
    def close(cls):
        cls.connection.close()

    @classmethod
    def connect(cls):
        profile = getAddonProfilePath()

        if not path.exists(profile):
            makedirs(profile)

        cls.connection = SqliteDatabase(path.join(profile, 'dramacool.db'))
        cls.connection.connect(True)

    @classmethod
    def create(cls):
        cls.connection.create_tables([RecentDrama, RecentFilter])
        cls.connection.commit()


class InternalDatabase(object):
    connection = None

    @classmethod
    def close(cls):
        cls.connection.close()

    @classmethod
    def connect(cls):
        cls.connection = SqliteDatabase(path.join(getAddonPath(), 'resources/data/dramacool.db'))
        cls.connection.connect(True)

    @classmethod
    def create(cls):
        from request import DramaDetailRequest, DramaListRequest

        cls.connection.create_tables([Drama])

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

        cls.connection.commit()


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
        self.setLabel(kwargs['title'])
        self.setArt({'thumb': kwargs['poster'],
                     'poster': kwargs['poster'],
                     'banner': kwargs['poster'],
                     'fanart': kwargs['poster'],
                     'clearart': kwargs['poster'],
                     'landscape': kwargs['poster'],
                     'icon': kwargs['poster']} if 'poster' in kwargs else {})
        self.setInfo('video', {label: kwargs[label] for label in ('title', 'plot', 'country', 'status', 'genre', 'year') if label in kwargs})


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
        self.setLabel(kwargs['title'])
        self.setArt({'icon': 'DefaultTVShows.png'})


if __name__ == '__main__':
    try:
        InternalDatabase.connect()
        InternalDatabase.create()
    finally:
        InternalDatabase.close()
