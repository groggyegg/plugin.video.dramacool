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

from functools import reduce
from json import dumps
from operator import or_

from resolveurl import resolve, resolver, scrape_supported
from xbmcext import Dialog, Keyboard, ListItem, Plugin, SortMethod, executebuiltin, getLocalizedString, sleep

from database import Drama, ExternalDatabase, InternalDatabase, RecentDrama, RecentFilter
from request import ConnectionError, Request

plugin = Plugin()


@plugin.route('/')
def home():
    plugin.addDirectoryItems([
        (plugin.getSerializedUrlFor('/search', type='movies'), ListItem(getLocalizedString(33000), iconImage='DefaultAddonsSearch.png'), True),
        (plugin.getSerializedUrlFor('/search', type='stars'), ListItem(getLocalizedString(33001), iconImage='DefaultAddonsSearch.png'), True),
        (plugin.getSerializedUrlFor('/recently-viewed'), ListItem(getLocalizedString(33002), iconImage='DefaultTags.png'), True),
        (plugin.getSerializedUrlFor('/recently-filtered'), ListItem(getLocalizedString(33011), iconImage='DefaultTags.png'), True),
        (plugin.getSerializedUrlFor('/recently-added', page=1), ListItem(getLocalizedString(33003), iconImage='DefaultRecentlyAddedEpisodes.png'), True),
        (plugin.getSerializedUrlFor('/recently-added-movie', page=1), ListItem(getLocalizedString(33004), iconImage='DefaultRecentlyAddedEpisodes.png'), True),
        (plugin.getSerializedUrlFor('/recently-added-kshow', page=1), ListItem(getLocalizedString(33005), iconImage='DefaultRecentlyAddedEpisodes.png'), True),
        (plugin.getSerializedUrlFor('/drama'), ListItem(getLocalizedString(33006), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/movies'), ListItem(getLocalizedString(33007), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/kshow'), ListItem(getLocalizedString(33008), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/most-popular-drama', page=1), ListItem(getLocalizedString(33009), iconImage='DefaultFavourites.png'), True),
        (plugin.getSerializedUrlFor('/list-star.html', page=1), ListItem(getLocalizedString(33010), iconImage='DefaultFavourites.png'), True)])
    plugin.endOfDirectory()


@plugin.route('/search')
def search(type):
    keyboard = Keyboard()
    keyboard.doModal()

    if keyboard.isConfirmed():
        plugin.redirect('/search', type=type, keyword=keyboard.getText(), page=1)


@plugin.route('/search')
def search_type(type, keyword, page):
    shows, pages = Request.search(plugin.getFullPath())
    items = []

    for path, title, poster in shows:
        item = Drama.get_or_none(Drama.path == path) if type == 'movies' else Drama(title=title, poster=poster)
        item = item if item else Drama.create(**Request.drama_detail(path))
        items.append((plugin.getSerializedUrlFor(path), item, True))

    items.extend(iter_pages(pages))

    if type == 'movies':
        plugin.setContent('tvshows')

    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/recently-viewed')
def recently_viewed():
    items = []

    for recent_drama in RecentDrama.select(RecentDrama.path).order_by(RecentDrama.timestamp.desc()):
        item = Drama.get_or_none(Drama.path == recent_drama.path)
        item = item if item else Drama.create(**Request.drama_detail(recent_drama.path))
        item.addContextMenuItems([(getLocalizedString(33100), 'RunPlugin({})'.format(plugin.getSerializedUrlFor('/recently-viewed', delete=item.path))),
                                  (getLocalizedString(33101), 'RunPlugin({})'.format(plugin.getSerializedUrlFor('/recently-viewed', delete='%')))])
        items.append((plugin.getUrlFor(item.path), item, True))

    plugin.setContent('tvshows')
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/recently-filtered')
def recently_filtered():
    items = []

    for recent_filter in RecentFilter.select(RecentFilter.path, RecentFilter.title).order_by(RecentFilter.timestamp.desc()):
        recent_filter.addContextMenuItems([(getLocalizedString(33100), 'RunPlugin({})'.format(plugin.getSerializedUrlFor('/recently-filtered', delete=recent_filter.path))),
                                           (getLocalizedString(33101), 'RunPlugin({})'.format(plugin.getSerializedUrlFor('/recently-filtered', delete='%')))])
        items.append((plugin.getUrlFor(recent_filter.path), recent_filter, True))

    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/recently-viewed')
def delete_recently_viewed(delete):
    RecentDrama.delete().where(RecentDrama.path ** delete).execute()
    executebuiltin('Container.Refresh')


@plugin.route('/recently-filtered')
def delete_recently_filtered(delete):
    RecentFilter.delete().where(RecentFilter.path ** delete).execute()
    executebuiltin('Container.Refresh')


@plugin.route('/recently-added')
@plugin.route('/recently-added-movie')
@plugin.route('/recently-added-kshow')
def recently_added(page):
    shows, pages = Request.recently_added(plugin.getFullPath())
    items = []

    for path, poster, title in shows:
        item = Drama.select().where(Drama.poster == poster).get_or_none()
        item = item if item else Drama(title=title, poster=poster)
        item.setProperty('IsPlayable', 'true')
        items.append((plugin.getSerializedUrlFor(path), item, False))

    items.extend(iter_pages(pages))
    plugin.setContent('episodes')
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/drama')
def drama():
    plugin.addDirectoryItems([
        (plugin.getSerializedUrlFor('/category/korean-drama'), ListItem(getLocalizedString(33200), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/japanese-drama'), ListItem(getLocalizedString(33201), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/taiwanese-drama'), ListItem(getLocalizedString(33202), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/hong-kong-drama'), ListItem(getLocalizedString(33203), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/chinese-drama'), ListItem(getLocalizedString(33204), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/other-asia-drama'), ListItem(getLocalizedString(33205), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/thailand-drama'), ListItem(getLocalizedString(33206), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/indian-drama'), ListItem(getLocalizedString(33207), iconImage='DefaultTVShows.png'), True)])
    plugin.endOfDirectory()


@plugin.route('/movies')
def movies():
    plugin.addDirectoryItems([
        (plugin.getSerializedUrlFor('/category/korean-movies'), ListItem(getLocalizedString(33300), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/japanese-movies'), ListItem(getLocalizedString(33301), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/taiwanese-movies'), ListItem(getLocalizedString(33302), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/hong-kong-movies'), ListItem(getLocalizedString(33303), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/chinese-movies'), ListItem(getLocalizedString(33304), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/american-movies'), ListItem(getLocalizedString(33305), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/other-asia-movies'), ListItem(getLocalizedString(33306), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/thailand-movies'), ListItem(getLocalizedString(33307), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/indian-movies'), ListItem(getLocalizedString(33308), iconImage='DefaultTVShows.png'), True)])
    plugin.endOfDirectory()


@plugin.route('/category/{}')
@plugin.route('/kshow')
def drama_filter():
    items = Dialog().multiselecttab(getLocalizedString(33400), {
        getLocalizedString(33401): ['#', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'],
        getLocalizedString(33402): [
            (getLocalizedString(33712), 33712),
            (getLocalizedString(33713), 33713),
            (getLocalizedString(33714), 33714),
            (getLocalizedString(33715), 33715),
            (getLocalizedString(33716), 33716),
            (getLocalizedString(33717), 33717),
            (getLocalizedString(33718), 33718),
            (getLocalizedString(33719), 33719),
            (getLocalizedString(33720), 33720),
            (getLocalizedString(33721), 33721),
            (getLocalizedString(33722), 33722)],
        getLocalizedString(33403): [
            (getLocalizedString(33709), 33709),
            (getLocalizedString(33710), 33710),
            (getLocalizedString(33711), 33711)],
        getLocalizedString(33404): ['2000', '2001', '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009',
                                    '2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019',
                                    '2020', '2021', '2022', '2023', '2024']})

    if items:
        for item in items.values():
            item.sort()

        characters = dumps(items[getLocalizedString(33401)])
        genres = dumps(items[getLocalizedString(33402)])
        statuses = dumps(items[getLocalizedString(33403)])
        years = dumps(items[getLocalizedString(33404)])
        plugin.redirect(f'{plugin.path}/{characters}/{genres}/{statuses}/{years}')


@plugin.route('/category/{}/{characters:json}/{genres:json}/{statuses:json}/{years:json}')
@plugin.route('/kshow/{characters:json}/{genres:json}/{statuses:json}/{years:json}')
def drama_list(characters, genres, statuses, years):
    expression = Drama.category == '/'.join(plugin.path.split('/')[:-4])

    if characters:
        expression &= reduce(or_, [~(Drama.title % '[a-zA-Z]*') if character == '#' else (Drama.title % (character + '*')) for character in characters])

    if genres:
        expression &= Drama.genre % ('*{}*'.format('*'.join(str(genre) for genre in genres)))

    if statuses:
        expression &= Drama.status << statuses

    if years:
        expression &= Drama.year << years

    RecentFilter.create(path=plugin.path, title=plugin.path)
    items = []

    for item in Drama.select().where(expression):
        items.append((plugin.getSerializedUrlFor(item.path), item, True))

    plugin.addSortMethods(SortMethod.TITLE, SortMethod.VIDEO_YEAR)
    plugin.setContent('tvshows')
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/most-popular-drama')
def popular_drama(page):
    shows, pages = Request.most_popular_drama(plugin.getFullPath())
    items = []

    for path in shows:
        item = Drama.get_or_none(Drama.path == path)
        item = item if item else Drama.create(**Request.drama_detail(path))
        items.append((plugin.getSerializedUrlFor(path), item, True))

    items.extend(iter_pages(pages))
    plugin.setContent('tvshows')
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/list-star.html')
def popular_star(page):
    stars, pages = Request.list_star(plugin.getFullPath())
    items = []

    for path, title, poster, plot in stars:
        item = Drama(title=title, poster=poster, plot=plot)
        items.append((plugin.getSerializedUrlFor(path), item, True))

    items.extend(iter_pages(pages))
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/star/{}')
def star():
    shows = Request.star(plugin.getFullPath())
    items = []

    for path in shows:
        item = Drama.get_or_none(Drama.path == path)
        item = item if item else Drama.create(**Request.drama_detail(path))
        items.append((plugin.getSerializedUrlFor(path), item, True))

    plugin.addSortMethods(SortMethod.TITLE, SortMethod.VIDEO_YEAR)
    plugin.setContent('tvshows')
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/drama-detail/{}')
def episode_list():
    items = []

    for path, title in Request.drama_detail_episode(plugin.getFullPath()):
        item = Drama(title=title)
        item.setProperty('IsPlayable', 'true')
        items.append((plugin.getSerializedUrlFor(path), item, False))

    plugin.setContent('episodes')
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory(cacheToDisc=False)


@plugin.route('/{:re("[^.]+.html")}')
def resolve_episode():
    title, path, servers = Request.video(plugin.getFullPath())
    servers = ['[COLOR orange]{}[/COLOR]'.format(server) if scrape_supported(video, '(.+)') else server for video, server in servers]
    position = Dialog().select(getLocalizedString(33500), servers)
    item = ListItem(title)
    url = False

    if position != -1:
        executebuiltin('ActivateWindow(busydialognocancel)')
        url = resolve(servers[position][0])

        if url:
            RecentDrama.create(path=path)
            item.setPath(url)
        else:
            Dialog().notification(getLocalizedString(33502), '')

        executebuiltin('Dialog.Close(busydialognocancel)')
    else:
        executebuiltin('Playlist.Clear')
        sleep(500)

    plugin.setResolvedUrl(bool(url), item)


def iter_pages(pages):
    for path, label in pages:
        item = ListItem(getLocalizedString(33601), iconImage='DefaultFolderBack.png') if label == '< Previous' else ListItem(getLocalizedString(33602))
        item.setProperty('SpecialSort', 'bottom')
        yield plugin.getUrlFor(path), item, True


if __name__ == '__main__':
    try:
        ExternalDatabase.connect()
        ExternalDatabase.create()
        InternalDatabase.connect()
        plugin()
    except (ConnectionError, resolver.ResolverError) as e:
        Dialog().notification(str(e), '')
    finally:
        ExternalDatabase.close()
        InternalDatabase.close()
