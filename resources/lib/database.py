from os import makedirs, remove
from os.path import exists

from peewee import CharField, Model, SmallIntegerField, SQL, SqliteDatabase, TextField
from playhouse.sqlite_ext import DateTimeField, JSONField

from xbmclib import Addon, ListItem, translatePath


class ExternalDatabase(object):
    profile = translatePath(Addon().getAddonInfo('profile'))
    connection = SqliteDatabase(profile + 'dramacool.db')
    connection_v1 = SqliteDatabase(profile + 'recently_viewed.db')

    @staticmethod
    def create():
        if not exists(ExternalDatabase.profile):
            makedirs(ExternalDatabase.profile)

        ExternalDatabase.connection.connect(True)
        ExternalDatabase.connection.create_tables([RecentDrama, RecentFilter])
        ExternalDatabase.migration_v1()
        ExternalDatabase.connection.commit()
        ExternalDatabase.connection.close()

    @staticmethod
    def migration_v1():
        if exists(ExternalDatabase.connection_v1.database):
            for recently_viewed in RecentlyViewed.select():
                RecentDrama.create(path=recently_viewed.path, timestamp=recently_viewed.last_visited)

            ExternalDatabase.connection_v1.close()
            remove(ExternalDatabase.connection_v1.database)


class InternalDatabase(object):
    connection = SqliteDatabase(translatePath(Addon().getAddonInfo('path')) + 'resources/data/dramacool.db')

    @staticmethod
    def create():
        import request
        from request.dramalist import DramaListParser
        from request.dramadetail import DramaDetailParser

        InternalDatabase.connection.connect(True)
        InternalDatabase.connection.create_tables([Drama])

        paths = {drama.path for drama in Drama.select()}

        for path in request.parse('/drama-list', DramaListParser):
            if path not in paths:
                request.parse(path, DramaDetailParser, path_=path)

        InternalDatabase.connection.commit()
        InternalDatabase.connection.close()


class ExternalModel(Model):
    class Meta:
        database = ExternalDatabase.connection


class InternalModel(Model):
    class Meta:
        database = InternalDatabase.connection


class Drama(InternalModel, ListItem):
    path = CharField(primary_key=True, constraints=[SQL('ON CONFLICT REPLACE')])
    poster = CharField(null=True)
    title = CharField()
    plot = CharField(null=True)
    country = CharField(null=True)
    genre = JSONField(null=True)
    year = SmallIntegerField(null=True)

    def __new__(cls, *args, **kwargs):
        return super(Drama, cls).__new__(cls)

    def __init__(self, *args, **kwargs):
        super(Drama, self).__init__(*args, **kwargs)
        self.setLabel(kwargs.pop('title'))
        self.setArt({'poster': kwargs.pop('poster')})
        self.setInfo('video', kwargs)


class RecentDrama(ExternalModel):
    path = CharField(primary_key=True, constraints=[SQL('ON CONFLICT REPLACE')])
    timestamp = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])


class RecentFilter(ExternalModel, ListItem):
    path = CharField()
    title = CharField(primary_key=True, constraints=[SQL('ON CONFLICT REPLACE')])
    timestamp = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

    def __new__(cls, *args, **kwargs):
        return super(RecentFilter, cls).__new__(cls)

    def __init__(self, *args, **kwargs):
        super(RecentFilter, self).__init__(*args, **kwargs)
        self.setLabel(kwargs.pop('title'))


class RecentlyViewed(Model):
    path = TextField(primary_key=True, constraints=[SQL('ON CONFLICT REPLACE')])
    last_visited = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

    class Meta:
        database = ExternalDatabase.connection_v1
        table_name = 'recently_viewed'


ExternalDatabase.create()
