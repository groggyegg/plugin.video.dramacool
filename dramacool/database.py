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
from os import makedirs
from os.path import join, exists

from peewee import CharField, Model, SmallIntegerField, SQL, SqliteDatabase
from playhouse.sqlite_ext import DateTimeField
from xbmcext import ListItem, getAddonPath, getAddonProfilePath, getLocalizedString

from request import Request

if __name__ == '__main__':
    from xbmcgui import ListItem


class JSONField(CharField):
    def db_value(self, value):
        if isinstance(value, str):
            return value
        else:
            return dumps(value)

    def python_value(self, value):
        return loads(value)


class ExternalDatabase(object):
    profile_path = getAddonProfilePath()
    connection = SqliteDatabase(join(profile_path, 'dramacool.db'))

    @classmethod
    def close(cls):
        cls.connection.close()

    @classmethod
    def connect(cls):
        if not exists(cls.profile_path):
            makedirs(cls.profile_path)

        cls.connection.connect(True)

    @classmethod
    def create(cls):
        cls.connection.create_tables([RecentDrama, RecentFilter])
        cls.connection.commit()


class InternalDatabase(object):
    addon_path = getAddonPath()
    connection = SqliteDatabase(join(addon_path if addon_path else '..', 'resources/data/dramacool.db'))

    @classmethod
    def close(cls):
        if cls.connection:
            cls.connection.close()

    @classmethod
    def connect(cls):
        cls.connection.connect(True)

    @classmethod
    def create(cls):
        cls.connection.create_tables([Drama])

        paths = {drama.path for drama in Drama.select().where((Drama.status == 33710))}
        categories = ['/category/korean-movies', '/category/japanese-movies', '/category/taiwanese-movies',
                      '/category/hong-kong-movies', '/category/chinese-movies', '/category/american-movies',
                      '/category/other-asia-movies', '/category/thailand-movies', '/category/indian-movies',
                      '/category/korean-drama', '/category/japanese-drama', '/category/taiwanese-drama',
                      '/category/hong-kong-drama', '/category/chinese-drama',
                      '/category/american-drama', '/category/other-asia-drama', '/category/thailand-drama',
                      '/category/indian-drama', '/kshow']

        for category in categories:
            for path in Request.drama_list(category):
                if path not in paths:
                    Drama.create(**Request.drama_detail(path), category=category)

        cls.connection.commit()


class ExternalModel(Model):
    class Meta:
        database = ExternalDatabase.connection


class InternalModel(Model):
    class Meta:
        database = InternalDatabase.connection


class Drama(InternalModel, ListItem):
    path = CharField(primary_key=True, constraints=[SQL('ON CONFLICT REPLACE')])
    category = CharField(null=True)
    poster = CharField()
    title = CharField()
    plot = CharField()
    country = SmallIntegerField()
    status = SmallIntegerField()
    genre = JSONField()
    year = SmallIntegerField()

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
        labels = {label: kwargs[label] for label in ['title', 'plot', 'year'] if label in kwargs}
        labels.update({label: getLocalizedString(kwargs[label]) for label in ['country', 'status'] if label in kwargs})
        labels.update({label: list(map(getLocalizedString, kwargs[label])) for label in ['genre'] if label in kwargs})
        self.setInfo('video', labels)


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
