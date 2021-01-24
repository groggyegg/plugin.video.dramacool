from dialog import FilterDialog
from plugin import url_for
from xbmcgui import Dialog, ListItem

import edb
import idb
import os
import plugin
import request
import resolveurl
import xbmc
import xbmcaddon
import xbmcplugin
import xbmcvfs

_addon = xbmcaddon.Addon()
_plugins = os.path.join(xbmcvfs.translatePath(_addon.getAddonInfo('path')), 'resources/lib/resolveurl/plugins')


@plugin.route('/')
def _():
    show([(url_for('/search?type=movies'), list_item(33000, 'DefaultAddonsSearch.png'), True),
          (url_for('/search?type=stars'), list_item(33001, 'DefaultAddonsSearch.png'), True),
          (url_for('/recently-viewed'), list_item(33002, 'DefaultUser.png'), True),
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
    keyboard = xbmc.Keyboard()
    keyboard.doModal()

    if keyboard.isConfirmed():
        plugin.redirect(f'{plugin.full_path}&keyword={keyboard.getText()}&page=1')


@plugin.route('/search', type='movies')
def _():
    items = []
    (dramalist, paginationlist) = request.parse(plugin.full_path, 'DramaPaginationListParser')
    idb.connect()

    for path in dramalist:
        (poster, info) = idb.fetchone(path)
        item = ListItem(info['title'])
        item.setArt({'poster': poster})
        item.setInfo('video', info)
        items.append((url_for(path), item, True))

    idb.close()
    append_pagination(items, paginationlist)
    show(items, 'tvshows')


@plugin.route('/search', type='stars')
def _():
    items = []
    (starlist, paginationlist) = request.parse(plugin.full_path, 'StarSearchPaginationListParser')

    for (path, poster, title) in starlist:
        item = ListItem(title)
        item.setArt({'poster': poster})
        items.append((url_for(path), item, True))

    append_pagination(items, paginationlist)
    show(items, 'artists')


@plugin.route('/recently-viewed', delete=False)
def _():
    edb.connect()
    idb.connect()
    items = []

    for path in edb.fetchall():
        (poster, info) = idb.fetchone(path)
        item = ListItem(info['title'])
        item.addContextMenuItems([(_addon.getLocalizedString(33100), f'RunPlugin({plugin.url}?delete={path})'),
                                  (_addon.getLocalizedString(33101), f'RunPlugin({plugin.url}?delete=%)')])
        item.setArt({'poster': poster})
        item.setInfo('video', info)
        items.append((url_for(path), item, True))

    edb.close()
    idb.close()
    show(items, 'tvshows')


@plugin.route('/recently-viewed', delete='(?P<delete>.+)')
def _(delete):
    edb.connect()
    edb.remove(delete)
    edb.close()
    xbmc.executebuiltin('Container.Refresh')


@plugin.route('/recently-added')
@plugin.route('/recently-added-movie')
@plugin.route('/recently-added-kshow')
def _():
    (recentlylist, paginationlist) = request.parse(plugin.full_path, 'RecentlyPaginationListParser')
    idb.connect()
    items = []

    for (path, poster, title) in recentlylist:
        item = ListItem(title)
        item.setArt({'poster': poster})
        item.setInfo('video', idb.fetchplot(poster))
        item.setProperty('IsPlayable', 'true')
        items.append((url_for(path), item, False))

    idb.close()
    append_pagination(items, paginationlist)
    show(items, 'tvshows')


@plugin.route('/drama-list')
def _():
    show([(url_for('/category/korean-drama'), list_item(33200), True),
          (url_for('/category/japanese-drama'), list_item(33201), True),
          (url_for('/category/taiwanese-drama'), list_item(33202), True),
          (url_for('/category/hong-kong-drama'), list_item(33203), True),
          (url_for('/category/chinese-drama'), list_item(33204), True),
          (url_for('/category/other-asia-drama'), list_item(33205), True),
          (url_for('/category/thailand-drama'), list_item(33206), True)])


@plugin.route('/drama-movie')
def _():
    show([(url_for('/category/korean-movies'), list_item(33300), True),
          (url_for('/category/japanese-movies'), list_item(33301), True),
          (url_for('/category/taiwanese-movies'), list_item(33302), True),
          (url_for('/category/hong-kong-movies'), list_item(33303), True),
          (url_for('/category/chinese-movies'), list_item(33304), True),
          (url_for('/category/american-movies'), list_item(33305), True),
          (url_for('/category/other-asia-movies'), list_item(33306), True),
          (url_for('/category/thailand-movies'), list_item(33307), True)])


@plugin.route('/category/[^/]+')
@plugin.route('/kshow')
def _():
    charlist, statuslist, yearlist = request.parse(plugin.path, 'FilterListParser')
    genrelist = ['Action', 'Adventure', 'Comedy', 'Crime', 'Drama', 'Fantasy', 'Horror', 'Mystery', 'Romance', 'Sci-fi', 'Thriller']
    dialog = FilterDialog(charlist, genrelist, statuslist, yearlist)
    dialog.doModal()

    if not dialog.cancelled:
        dramalist = request.parse(plugin.path, 'CharGenreStatusYearDramaListParser', **dialog.result())
        idb.connect()
        items = []

        for (path, poster, info) in idb.fetchall(dramalist):
            item = ListItem(info['title'])
            item.setArt({'poster': poster})
            item.setInfo('video', info)
            items.append((url_for(path), item, True))

        idb.close()
        show(items, 'tvshows', True)


@plugin.route('/most-popular-drama')
def _():
    (dramalist, paginationlist) = request.parse(plugin.full_path, 'DramaPaginationListParser')
    idb.connect()
    items = []

    for path in dramalist:
        (poster, info) = idb.fetchone(path)
        item = ListItem(info['title'])
        item.setArt({'poster': poster})
        item.setInfo('video', info)
        items.append((url_for(path), item, True))

    idb.close()
    append_pagination(items, paginationlist)
    show(items, 'tvshows')


@plugin.route('/list-star.html')
def _():
    (starlist, paginationlist) = request.parse(plugin.full_path, 'StarPaginationListParser')
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
    idb.connect()
    items = []

    for (path, poster, info) in idb.fetchall(request.parse(plugin.path, 'StarDramaListParser')):
        item = ListItem(info['title'])
        item.setArt({'poster': poster})
        item.setInfo('video', info)
        items.append((url_for(path), item, True))

    idb.close()
    show(items, 'tvshows', True)


@plugin.route('/drama-detail/[^/]+')
def _():
    items = []

    for (path, title) in request.parse(plugin.path, 'EpisodeListParser'):
        item = ListItem(title)
        item.setInfo('video', {})
        item.setProperty('IsPlayable', 'true')
        items.append((url_for(path), item, False))

    show(items, 'episodes')


@plugin.route('/[^/]+.html')
def _():
    (path, serverlist, titlelist, title) = request.parse(plugin.path, 'ServerListParser')
    position = Dialog().select(_addon.getLocalizedString(33500), titlelist)
    item = ListItem(title)
    url = False

    if position != -1:
        xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
        resolveurl.add_plugin_dirs(_plugins)

        try:
            url = resolveurl.resolve(serverlist[position])

            if url:
                edb.connect()
                edb.add(path)
                edb.close()
                item.setPath(url)
                subtitle = request.subtitle(serverlist[position])

                if subtitle:
                    item.setSubtitles([subtitle])
            else:
                Dialog().notification(_addon.getLocalizedString(33502), '')
        except:
            Dialog().notification(_addon.getLocalizedString(33501), '')

        xbmc.executebuiltin('Dialog.Close(busydialognocancel)')
    else:
        xbmc.executebuiltin('Playlist.Clear')
        xbmc.sleep(500)

    xbmcplugin.setResolvedUrl(plugin.handle, isinstance(url, str), item)


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
        xbmcplugin.setContent(plugin.handle, content)

    if sort:
        xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)

    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


if __name__ == '__main__':
    plugin.run()
