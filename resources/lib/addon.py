import os
from functools import reduce
from json import loads, dumps
from operator import or_
from urllib.parse import quote

import plugin
import resolveurl
from database import Drama, RecentDrama, RecentFilter, ExternalDatabase, InternalDatabase
from dialog import FilterDialog
from plugin import url_for
from request import RecentlyDramaRequest, SearchRequest, StarListRequest, StarDramaRequest, DramaDetailRequest, EpisodeListRequest, ServerListRequest
from xbmclib import *

_plugins = os.path.join(translatePath(getAddonInfo('path')), 'resources/lib/resolveurl/plugins')


@plugin.route('/')
def _():
    show([(url_for('/search?type=movies'), list_item(33000, 'DefaultAddonsSearch.png'), True),
          (url_for('/search?type=stars'), list_item(33001, 'DefaultAddonsSearch.png'), True),
          (url_for('/recently-viewed'), list_item(33002, 'DefaultTags.png'), True),
          (url_for('/recently-filtered'), list_item(33011, 'DefaultTags.png'), True),
          (url_for('/recently-added?page=1'), list_item(33003, 'DefaultRecentlyAddedEpisodes.png'), True),
          (url_for('/recently-added-movie?page=1'), list_item(33004, 'DefaultRecentlyAddedEpisodes.png'), True),
          (url_for('/recently-added-kshow?page=1'), list_item(33005, 'DefaultRecentlyAddedEpisodes.png'), True),
          (url_for('/drama-list'), list_item(33006, 'DefaultTVShows.png'), True),
          (url_for('/drama-movie'), list_item(33007, 'DefaultTVShows.png'), True),
          (url_for('/kshow?label=33008'), list_item(33008, 'DefaultTVShows.png'), True),
          (url_for('/most-popular-drama?page=1'), list_item(33009, 'DefaultFavourites.png'), True),
          (url_for('/list-star.html?page=1'), list_item(33010, 'DefaultFavourites.png'), True)])


@plugin.route('/search', type=True, keyword=False)
def _():
    keyboard = Keyboard()
    keyboard.doModal()

    if keyboard.isConfirmed():
        plugin.redirect(plugin.full_path + '&keyword=' + keyboard.getText() + '&page=1')


@plugin.route('/search', type='movies')
def _():
    dramas, pagination = SearchRequest().get(plugin.full_path)
    items = []

    for path, title, poster in dramas:
        item = Drama.get_or_none(Drama.path == path)
        items.append((url_for(path), item if item else Drama.create(**DramaDetailRequest().get(path)), True))

    append_pagination(items, pagination)
    show(items, 'tvshows')


@plugin.route('/search', type='stars')
def _():
    stars, pagination = SearchRequest().get(plugin.full_path)
    items = []

    for path, title, poster in stars:
        item = Drama(title=title, poster=poster)
        items.append((url_for(path), item, True))

    append_pagination(items, pagination)
    show(items, 'artists')


@plugin.route('/recently-viewed', delete=False)
def _():
    items = []

    for recent_drama in RecentDrama.select(RecentDrama.path).order_by(RecentDrama.timestamp.desc()):
        item = Drama.get_or_none(Drama.path == recent_drama.path)
        item = item if item else Drama.create(**DramaDetailRequest().get(recent_drama.path))
        item.addContextMenuItems([(getLocalizedString(33100), 'RunPlugin(' + plugin.url + '?delete=' + item.path + ')'),
                                  (getLocalizedString(33101), 'RunPlugin(' + plugin.url + '?delete=%)')])
        items.append((url_for(item.path), item, True))

    show(items, 'tvshows')


@plugin.route('/recently-viewed', delete='(?P<delete>.+)')
def _(delete):
    RecentDrama.delete().where(RecentDrama.path ** delete).execute()
    executebuiltin('Container.Refresh')


@plugin.route('/recently-filtered', delete=False)
def _():
    items = []

    for recent_filter in RecentFilter.select(RecentFilter.path, RecentFilter.title).order_by(RecentFilter.timestamp.desc()):
        recent_filter.addContextMenuItems([(getLocalizedString(33100), 'RunPlugin(' + plugin.url + '?delete=' + recent_filter.path + ')'),
                                           (getLocalizedString(33101), 'RunPlugin(' + plugin.url + '?delete=%)')])
        items.append((url_for(recent_filter.path), recent_filter, True))

    show(items, 'tvshows')


@plugin.route('/recently-filtered', delete='(?P<delete>.+)')
def _(delete):
    RecentFilter.delete().where(RecentFilter.path.contains(delete)).execute()
    executebuiltin('Container.Refresh')


@plugin.route('/recently-added')
@plugin.route('/recently-added-movie')
@plugin.route('/recently-added-kshow')
def _():
    episodes, pagination = RecentlyDramaRequest().get(plugin.full_path)
    items = []

    for (path, poster, dateadded, title) in episodes:
        item = Drama.select().where(Drama.poster == poster).get_or_none()
        item = Drama(title=title, poster=poster, dateadded=dateadded, **{'plot': item.plot} if item else {})
        item.setProperty('IsPlayable', 'true')
        items.append((url_for(path), item, False))

    append_pagination(items, pagination)
    show(items, 'tvshows')


@plugin.route('/drama-list')
def _():
    show([(url_for('/category/korean-drama?label=33200'), list_item(33200), True),
          (url_for('/category/japanese-drama?label=33201'), list_item(33201), True),
          (url_for('/category/taiwanese-drama?label=33202'), list_item(33202), True),
          (url_for('/category/hong-kong-drama?label=33203'), list_item(33203), True),
          (url_for('/category/chinese-drama?label=33204'), list_item(33204), True),
          (url_for('/category/other-asia-drama?label=33205'), list_item(33205), True),
          (url_for('/category/thailand-drama?label=33206'), list_item(33206), True),
          (url_for('/category/indian-drama?label=33207'), list_item(33207), True)])


@plugin.route('/drama-movie')
def _():
    show([(url_for('/category/korean-movies?label=33300'), list_item(33300), True),
          (url_for('/category/japanese-movies?label=33301'), list_item(33301), True),
          (url_for('/category/taiwanese-movies?label=33302'), list_item(33302), True),
          (url_for('/category/hong-kong-movies?label=33303'), list_item(33303), True),
          (url_for('/category/chinese-movies?label=33304'), list_item(33304), True),
          (url_for('/category/american-movies?label=33305'), list_item(33305), True),
          (url_for('/category/other-asia-movies?label=33306'), list_item(33306), True),
          (url_for('/category/thailand-movies?label=33307'), list_item(33307), True),
          (url_for('/category/indian-movies?label=33308'), list_item(33308), True)])


@plugin.route('/category/[^/]+', filterstr=False)
@plugin.route('/kshow', filterstr=False)
def _():
    characters = ['#', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                  'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    genres = ['Action', 'Adventure', 'Comedy', 'Crime', 'Drama', 'Fantasy',
              'Horror', 'Mystery', 'Romance', 'Sci-fi', 'Thriller']
    statuses = ['Ongoing', 'Completed', 'Upcoming']
    years = ['2000', '2001', '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011',
             '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022']

    dialog = FilterDialog(characters, genres, statuses, years)
    dialog.doModal()

    if not dialog.cancelled:
        plugin.redirect(plugin.full_path + '&filterstr=' + quote(dumps(dialog.result())))


@plugin.route('/category/[^/]+', label='(?P<label>.+)', filterstr='(?P<filterstr>.+)')
@plugin.route('/kshow', label='(?P<label>.+)', filterstr='(?P<filterstr>.+)')
def _(label, filterstr):
    filters = loads(filterstr)
    expr = Drama.mediatype == plugin.path

    if filters['chars']:
        expr &= reduce(or_, [~(Drama.title % '[a-zA-Z]*') if char == '#' else (Drama.title % (char + '*')) for char in filters['chars']])

    if filters['years']:
        expr &= Drama.year << filters['years']

    if filters['genres']:
        expr &= Drama.genre % ('*' + '*'.join(genre for genre in filters['genres']) + '*')

    if filters['statuses']:
        expr &= Drama.status << filters['statuses']

    title = '[{}] Character: {} Year: {} Genre: {} Status: {}'.format(getLocalizedString(int(label)),
                                                                      str(filters['chars']),
                                                                      str(filters['years']),
                                                                      str(filters['genres']),
                                                                      str(filters['statuses']))

    RecentFilter.create(path=plugin.full_path, title=title)
    items = []

    for item in Drama.select().where(expr):
        items.append((url_for(item.path), item, True))

    show(items, 'tvshows', True)


@plugin.route('/most-popular-drama')
def _():
    dramas, pagination = SearchRequest().get(plugin.full_path)
    items = []

    for path, title, poster in dramas:
        item = Drama.get_or_none(Drama.path == path)
        item = item if item else Drama(title=title, poster=poster)
        items.append((url_for(path), item, True))

    append_pagination(items, pagination)
    show(items, 'tvshows')


@plugin.route('/list-star.html')
def _():
    stars, pagination = StarListRequest().get(plugin.full_path)
    items = []

    for (path, title, poster, plot) in stars:
        item = Drama(title=title, poster=poster, plot=plot)
        items.append((url_for(path), item, True))

    append_pagination(items, pagination)
    show(items)


@plugin.route('/star/[^/]+')
def _():
    dramas = StarDramaRequest().get(plugin.path)
    items = []

    for path, title, poster in dramas:
        item = Drama.get_or_none(Drama.path == path)
        items.append((url_for(path), item if item else Drama(title=title, poster=poster), True))

    show(items, 'tvshows', True)


@plugin.route('/drama-detail/[^/]+')
def _():
    items = []

    for path, title in EpisodeListRequest().get(plugin.path):
        item = Drama(title=title)
        item.setProperty('IsPlayable', 'true')
        items.append((url_for(path), item, False))

    show(items, 'episodes')


@plugin.route('/[^/]+.html')
def _():
    request = ServerListRequest()
    title, path, servers = request.get(plugin.path)
    position = Dialog().select(getLocalizedString(33500), [name for video, name in servers])
    item = ListItem(title)
    url = False

    if position != -1:
        executebuiltin('ActivateWindow(busydialognocancel)')
        resolveurl.add_plugin_dirs(_plugins)

        try:
            url = resolveurl.resolve(servers[position][0])

            if url:
                RecentDrama.create(path=path)
                item.setPath(url)
                subtitle = request.get_subtitle(servers[position][0])

                if subtitle:
                    item.setSubtitles([subtitle])
            else:
                Dialog().notification(getLocalizedString(33502), '')
        except:
            Dialog().notification(getLocalizedString(33501), '')

        executebuiltin('Dialog.Close(busydialognocancel)')
    else:
        executebuiltin('Playlist.Clear')
        sleep(500)

    setResolvedUrl(plugin.handle, isinstance(url, str), item)


def append_pagination(items, paginationlist):
    for (query, title) in paginationlist:
        item = list_item(label=title) if '>' in title else list_item(label=title, icon='DefaultFolderBack.png')
        item.setProperty('SpecialSort', 'bottom')
        items.append((url_for(query), item, True))


def list_item(id=None, icon=None, label=None):
    item = ListItem(getLocalizedString(id) if id else label)
    item.setArt({'icon': icon})
    return item


def show(items, content=None, sort=False):
    if content:
        setContent(plugin.handle, content)

    if sort:
        addSortMethod(plugin.handle, SORT_METHOD_TITLE)
        addSortMethod(plugin.handle, SORT_METHOD_VIDEO_YEAR)

    addDirectoryItems(plugin.handle, items, len(items))
    endOfDirectory(plugin.handle)


if __name__ == '__main__':
    try:
        ExternalDatabase.connect()
        ExternalDatabase.create()
        InternalDatabase.connect()
        plugin.run()
    finally:
        ExternalDatabase.close()
        InternalDatabase.close()
