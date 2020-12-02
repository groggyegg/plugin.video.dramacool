from plugin import url_for
from xbmcgui import Dialog, ListItem

import base64
import edb
import idb
import os
import parser
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


@plugin.route(r'/search\?type=(movies|stars)')
def _():
    keyboard = xbmc.Keyboard()
    keyboard.doModal()

    if keyboard.isConfirmed():
        plugin.redirect(plugin.pathquery + '&keyword=' + keyboard.getText() + '&page=1')


@plugin.route(r'/search\?((type=(?P<type>movies|stars)|page=[^&]+|keyword=[^&]+)&?)+', 1)
def _(type):
    items = []

    if type == 'movies':
        (dramalist, paginationlist) = parser.DramaPaginationListParser().parse(request.get(plugin.pathquery))
        idb.connect()

        for path in dramalist:
            (poster, info) = idb.fetchone(path)
            item = ListItem(info['title'])
            item.setArt({'poster': poster})
            item.setInfo('video', info)
            items.append((url_for(path), item, True))

        idb.close()
    else:
        (starlist, paginationlist) = parser.StarSearchPaginationListParser().parse(request.get(plugin.pathquery))

        for (path, poster, title) in starlist:
            item = ListItem(title)
            item.setArt({'poster': poster})
            items.append((url_for(path), item, True))

    append_pagination(items, paginationlist)
    show(items, 'tvshows')


@plugin.route('/recently-viewed')
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


@plugin.route(r'/recently-viewed\?delete=(?P<delete>.+)')
def _(delete):
    edb.connect()
    edb.remove(delete)
    edb.close()
    xbmc.executebuiltin('Container.Refresh')


@plugin.route(r'/recently-added\?page=[^&]+')
@plugin.route(r'/recently-added-movie\?page=[^&]+')
@plugin.route(r'/recently-added-kshow\?page=[^&]+')
def _():
    (recentlylist, paginationlist) = parser.RecentlyPaginationListParser().parse(request.get(plugin.pathquery))
    items = []

    for (path, poster, title) in recentlylist:
        item = ListItem(title)
        item.setArt({'poster': poster})
        item.setInfo('video', {})
        item.setProperty('IsPlayable', 'true')
        items.append((url_for(path), item, False))

    append_pagination(items, paginationlist)
    show(items, 'episodes')


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
    show([(url_for(f'{plugin.path}/char'), list_item(33400), True),
          (url_for(f'{plugin.path}/genre'), list_item(33401), True),
          (url_for(f'{plugin.path}/status'), list_item(33402), True),
          (url_for(f'{plugin.path}/year'), list_item(33403), True)])


@plugin.route('(?P<path>/category/[^/]+)/(?P<selectid>[^/]+)')
@plugin.route('(?P<path>/kshow)/(?P<selectid>[^/]+)')
def _(path, selectid):
    items = []

    if selectid == 'char':
        filterlist = parser.CharFilterListParser().parse(request.get(path))
    elif selectid == 'genre':
        filterlist = ['Action', 'Adventure', 'Comedy', 'Crime', 'Drama', 'Fantasy', 'Horror', 'Mystery', 'Romance', 'Sci-fi', 'Thriller']
    elif selectid == 'status':
        filterlist = parser.StatusFilterListParser().parse(request.get(path))
    else:
        filterlist = parser.YearFilterListParser().parse(request.get(path))

    for selectvalue in filterlist:
        item = ListItem(selectvalue)
        items.append((url_for(f'{plugin.path}/{base64.b64encode(selectvalue.encode()).decode()}'), item, True))

    show(items)


@plugin.route('(?P<path>/category/[^/]+)/(?P<selectid>[^/]+)/(?P<selectvalue>[^/]+)')
@plugin.route('(?P<path>/kshow)/(?P<selectid>[^/]+)/(?P<selectvalue>[^/]+)')
def _(path, selectid, selectvalue):
    selectvalue = base64.b64decode(selectvalue).decode('ascii')
    idb.connect()
    items = []

    if selectid == 'char':
        dramalist = parser.CharDramaListParser(selectvalue).parse(request.get(path))
    elif selectid == 'genre':
        dramalist = parser.GenreDramaListParser(selectvalue).parse(request.get(path))
    elif selectid == 'status':
        dramalist = parser.StatusDramaListParser(selectvalue).parse(request.get(path))
    else:
        dramalist = parser.YearDramaListParser(selectvalue).parse(request.get(path))

    for (path, poster, info) in idb.fetchall(dramalist):
        item = ListItem(info['title'])
        item.setArt({'poster': poster})
        item.setInfo('video', info)
        items.append((url_for(path), item, True))

    idb.close()
    show(items, 'tvshows', True)


@plugin.route(r'/most-popular-drama\?page=[^&]+')
def _():
    (dramalist, paginationlist) = parser.DramaPaginationListParser().parse(request.get(plugin.pathquery))
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


@plugin.route(r'/list-star.html\?page=[^&]+')
def _():
    (starlist, paginationlist) = parser.StarPaginationListParser().parse(request.get(plugin.pathquery))
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

    for (path, poster, info) in idb.fetchall(parser.StarDramaListParser().parse(request.get(plugin.path))):
        item = ListItem(info['title'])
        item.setArt({'poster': poster})
        item.setInfo('video', info)
        items.append((url_for(path), item, True))

    idb.close()
    show(items, 'tvshows', True)


@plugin.route('/drama-detail/[^/]+')
def _():
    items = []

    for (path, title) in parser.EpisodeListParser().parse(request.get(plugin.path)):
        item = ListItem(title)
        item.setInfo('video', {})
        item.setProperty('IsPlayable', 'true')
        items.append((url_for(path), item, False))

    show(items, 'episodes')


@plugin.route('/[^/]+.html', 1)
def _():
    (path, serverlist, titlelist, title) = parser.ServerListParser().parse(request.get(plugin.path))
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

                if subtitle is not None:
                    if isinstance(subtitle, int):
                        Dialog().notification(_addon.getLocalizedString(subtitle), '')
                    else:
                        item.setSubtitles([subtitle])
            else:
                Dialog().notification(_addon.getLocalizedString(33502), '')
        except resolveurl.resolver.ResolverError:
            Dialog().notification(_addon.getLocalizedString(33501), '')

        xbmc.executebuiltin('Dialog.Close(busydialognocancel)')

    xbmcplugin.setResolvedUrl(plugin.handle, url is not False, item)


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
    if content is not None:
        xbmcplugin.setContent(plugin.handle, content)

    if sort:
        xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)

    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


if __name__ == '__main__':
    plugin.run()
