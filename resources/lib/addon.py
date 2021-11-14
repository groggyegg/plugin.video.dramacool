import os
from json import loads, dumps

import plugin
import request
import resolveurl
from database import Drama, RecentDrama, RecentFilter
from dialog import FilterDialog
from plugin import url_for
from request.dramadetail import DramaDetailParser
from request.dramalist import CharGenreStatusYearDramaListParser
from request.dramapaginationlist import DramaPaginationListParser
from request.episodelist import EpisodeListParser
from request.filterlist import FilterListParser
from request.recentlypaginationlist import RecentlyPaginationListParser
from request.serverlist import ServerListParser
from request.stardramalist import StarDramaListParser
from request.starpaginationlist import StarPaginationListParser
from request.starsearchpaginationlist import StarSearchPaginationListParser
from xbmclib import *

_addon = Addon()
_plugins = os.path.join(translatePath(_addon.getAddonInfo('path')), 'resources/lib/resolveurl/plugins')


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
          (url_for('/kshow'), list_item(33008, 'DefaultTVShows.png'), True),
          (url_for('/most-popular-drama?page=1'), list_item(33009, 'DefaultFavourites.png'), True),
          (url_for('/list-star.html?page=1'), list_item(33010, 'DefaultFavourites.png'), True)])


@plugin.route('/search', type=True, keyword=False)
def _():
    keyboard = Keyboard()
    keyboard.doModal()

    if keyboard.isConfirmed():
        plugin.redirect(f'{plugin.full_path}&keyword={keyboard.getText()}&page=1')


@plugin.route('/search', type='movies')
def _():
    items = []
    (dramalist, paginationlist) = request.parse(plugin.full_path, DramaPaginationListParser)

    for path in dramalist:
        item = Drama.get_or_none(Drama.path == path)
        items.append((url_for(path), item if item else request.parse(path, DramaDetailParser, path_=path), True))

    append_pagination(items, paginationlist)
    show(items, 'tvshows')


@plugin.route('/search', type='stars')
def _():
    items = []
    (starlist, paginationlist) = request.parse(plugin.full_path, StarSearchPaginationListParser)

    for (path, poster, title) in starlist:
        item = ListItem(title)
        item.setArt({'poster': poster})
        items.append((url_for(path), item, True))

    append_pagination(items, paginationlist)
    show(items, 'artists')


@plugin.route('/recently-viewed', delete=False)
def _():
    items = []

    for recent_drama in RecentDrama.select(RecentDrama.path).order_by(RecentDrama.timestamp.desc()):
        item = Drama.get_or_none(Drama.path == recent_drama.path)
        item = item if item else request.parse(recent_drama.path, DramaDetailParser, path_=recent_drama.path)
        item.addContextMenuItems([(_addon.getLocalizedString(33100), f'RunPlugin({plugin.url}?delete={item.path})'),
                                  (_addon.getLocalizedString(33101), f'RunPlugin({plugin.url}?delete=%)')])
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
        recent_filter.addContextMenuItems([(_addon.getLocalizedString(33100), f'RunPlugin({plugin.url}?delete={recent_filter.path})'),
                                           (_addon.getLocalizedString(33101), f'RunPlugin({plugin.url}?delete=%)')])
        items.append((url_for(recent_filter.path), recent_filter, True))

    show(items, 'tvshows')


@plugin.route('/recently-filtered', delete='(?P<delete>.+)')
def _(delete):
    RecentFilter.delete().where(RecentFilter.path ** delete).execute()
    executebuiltin('Container.Refresh')


@plugin.route('/recently-added')
@plugin.route('/recently-added-movie')
@plugin.route('/recently-added-kshow')
def _():
    (recentlylist, paginationlist) = request.parse(plugin.full_path, RecentlyPaginationListParser)
    items = []

    for (path, poster, title) in recentlylist:
        item = Drama.get_or_none(Drama.poster == poster)

        if item is None:
            item = ListItem(title)
            item.setArt({'poster': poster})
            item.setInfo('video', {})

        item.setProperty('IsPlayable', 'true')
        items.append((url_for(path), item, False))

    append_pagination(items, paginationlist)
    show(items, 'tvshows')


@plugin.route('/drama-list')
def _():
    show([(url_for(f'/category/korean-drama?label={33200}'), list_item(33200), True),
          (url_for(f'/category/japanese-drama?label={33201}'), list_item(33201), True),
          (url_for(f'/category/taiwanese-drama?label={33202}'), list_item(33202), True),
          (url_for(f'/category/hong-kong-drama?label={33203}'), list_item(33203), True),
          (url_for(f'/category/chinese-drama?label={33204}'), list_item(33204), True),
          (url_for(f'/category/other-asia-drama?label={33205}'), list_item(33205), True),
          (url_for(f'/category/thailand-drama?label={33206}'), list_item(33206), True)])


@plugin.route('/drama-movie')
def _():
    show([(url_for(f'/category/korean-movies?label={33300}'), list_item(33300), True),
          (url_for(f'/category/japanese-movies?label={33301}'), list_item(33301), True),
          (url_for(f'/category/taiwanese-movies?label={33302}'), list_item(33302), True),
          (url_for(f'/category/hong-kong-movies?label={33303}'), list_item(33303), True),
          (url_for(f'/category/chinese-movies?label={33304}'), list_item(33304), True),
          (url_for(f'/category/american-movies?label={33305}'), list_item(33305), True),
          (url_for(f'/category/other-asia-movies?label={33306}'), list_item(33306), True),
          (url_for(f'/category/thailand-movies?label={33307}'), list_item(33307), True)])


@plugin.route('/category/[^/]+', filterstr=False)
@plugin.route('/kshow', filterstr=False)
def _():
    charlist, statuslist, yearlist = request.parse(plugin.path, FilterListParser)
    genrelist = ['Action', 'Adventure', 'Comedy', 'Crime', 'Drama', 'Fantasy', 'Horror', 'Mystery', 'Romance', 'Sci-fi', 'Thriller']
    dialog = FilterDialog(charlist, genrelist, statuslist, yearlist)
    dialog.doModal()

    if not dialog.cancelled:
        plugin.redirect(f'{plugin.full_path}&filterstr={dumps(dialog.result())}')


@plugin.route('/category/[^/]+', label='(?P<label>.+)', filterstr='(?P<filterstr>.+)')
@plugin.route('/kshow', label='(?P<label>.+)', filterstr='(?P<filterstr>.+)')
def _(label, filterstr):
    filterdict = loads(filterstr)
    chars = filterdict["chars"]
    years = filterdict["years"]
    genres = filterdict["genres"]
    statuses = filterdict["statuses"]

    title = f'[{_addon.getLocalizedString(int(label))}] Character: {chars} Year: {years} Genre: {genres} Status: {statuses}'
    RecentFilter.create(path=plugin.full_path, title=title)
    paths = request.parse(plugin.path, CharGenreStatusYearDramaListParser, chars=chars, years=years, genres=genres, statuses=statuses)
    items = []

    for drama in Drama.select().where(Drama.path << paths):
        paths.discard(drama.path)
        items.append((url_for(drama.path), drama, True))

    for path in paths:
        drama = request.parse(path, DramaDetailParser, path_=path)
        items.append((url_for(path), drama, True))

    show(items, 'tvshows', True)


@plugin.route('/most-popular-drama')
def _():
    (dramalist, paginationlist) = request.parse(plugin.full_path, DramaPaginationListParser)
    items = []

    for path in dramalist:
        item = Drama.get_or_none(Drama.path == path)
        item = item if item else request.parse(path, DramaDetailParser, path_=path)
        items.append((url_for(path), item, True))

    append_pagination(items, paginationlist)
    show(items, 'tvshows')


@plugin.route('/list-star.html')
def _():
    (starlist, paginationlist) = request.parse(plugin.full_path, StarPaginationListParser)
    items = []

    for (path, poster, title, plot) in starlist:
        item = ListItem(title)
        item.setArt({'poster': poster})
        item.setInfo('video', {'plot': plot})
        items.append((url_for(path), item, True))

    append_pagination(items, paginationlist)
    show(items)


@plugin.route('/star/[^/]+')
def _():
    items = []
    paths = request.parse(plugin.path, StarDramaListParser)

    for drama in Drama.select().where(Drama.path in paths):
        paths.discard(drama.path)
        items.append((url_for(drama.path), drama, True))

    for path in paths:
        item = request.parse(path, DramaDetailParser, path_=path)
        items.append((url_for(path), item, True))

    show(items, 'tvshows', True)


@plugin.route('/drama-detail/[^/]+')
def _():
    items = []

    for (path, title) in request.parse(plugin.path, EpisodeListParser):
        item = ListItem(title)
        item.setInfo('video', {})
        item.setProperty('IsPlayable', 'true')
        items.append((url_for(path), item, False))

    show(items, 'episodes')


@plugin.route('/[^/]+.html')
def _():
    (path, serverlist, titlelist, title) = request.parse(plugin.path, ServerListParser)
    position = Dialog().select(_addon.getLocalizedString(33500), titlelist)
    item = ListItem(title)
    url = False

    if position != -1:
        executebuiltin('ActivateWindow(busydialognocancel)')
        resolveurl.add_plugin_dirs(_plugins)

        try:
            url = resolveurl.resolve(serverlist[position])

            if url:
                RecentDrama.create(path=path)
                item.setPath(url)
                subtitle = request.subtitle(serverlist[position])

                if subtitle:
                    item.setSubtitles([subtitle])
            else:
                Dialog().notification(_addon.getLocalizedString(33502), '')
        except:
            Dialog().notification(_addon.getLocalizedString(33501), '')

        executebuiltin('Dialog.Close(busydialognocancel)')
    else:
        executebuiltin('Playlist.Clear')
        sleep(500)

    setResolvedUrl(plugin.handle, isinstance(url, str), item)


def append_pagination(items, paginationlist):
    for (query, title) in paginationlist:
        item = list_item(33600) if title == 'next' else list_item(33601, 'DefaultFolderBack.png')
        item.setProperty('SpecialSort', 'bottom')
        items.append((url_for(plugin.path + query), item, True))


def list_item(id, icon=None):
    item = ListItem(_addon.getLocalizedString(id))
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
    plugin.run()
