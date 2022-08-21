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

from resolveurl import resolve, scrape_supported
from resolveurl.resolver import ResolverError
from xbmc import Keyboard, executebuiltin, sleep
from xbmcext import Dialog, ListItem, Plugin, getLocalizedString
from xbmcplugin import SORT_METHOD_TITLE, SORT_METHOD_VIDEO_YEAR
from xbmcaddon import Addon

from database import Drama, ExternalDatabase, InternalDatabase, RecentDrama, RecentFilter
from request import RecentlyDramaRequest, SearchRequest, StarListRequest, StarDramaRequest, DramaDetailRequest, EpisodeListRequest, ServerListRequest, SubtitleRequest
import resolveurl
import os
import xbmcvfs

plugin = Plugin()
__plugins__ = os.path.join(xbmcvfs.translatePath(Addon().getAddonInfo('path')), 'dramacool/resolveurl/plugins')
resolveurl.add_plugin_dirs(__plugins__)


@plugin.route('/')
def home():
    plugin.setDirectoryItems([(plugin.getUrlFor('/search', type='movies'), ListItem(33000, iconImage='DefaultAddonsSearch.png'), True),
                              (plugin.getUrlFor('/search', type='stars'), ListItem(33001, iconImage='DefaultAddonsSearch.png'), True),
                              (plugin.getUrlFor('/recently-viewed'), ListItem(33002, iconImage='DefaultTags.png'), True),
                              (plugin.getUrlFor('/recently-filtered'), ListItem(33011, iconImage='DefaultTags.png'), True),
                              (plugin.getUrlFor('/recently-added', page=1), ListItem(33003, iconImage='DefaultRecentlyAddedEpisodes.png'), True),
                              (plugin.getUrlFor('/recently-added-movie', page=1), ListItem(33004, iconImage='DefaultRecentlyAddedEpisodes.png'), True),
                              (plugin.getUrlFor('/recently-added-kshow', page=1), ListItem(33005, iconImage='DefaultRecentlyAddedEpisodes.png'), True),
                              (plugin.getUrlFor('/drama-list'), ListItem(33006, iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/drama-movie'), ListItem(33007, iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/kshow', label=33008), ListItem(33008, iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/most-popular-drama', page=1), ListItem(33009, iconImage='DefaultFavourites.png'), True),
                              (plugin.getUrlFor('/list-star.html', page=1), ListItem(33010, iconImage='DefaultFavourites.png'), True)])


@plugin.route('/search')
def search(type):
    keyboard = Keyboard()
    keyboard.doModal()

    if keyboard.isConfirmed():
        plugin.redirect('/search', type=type, keyword=keyboard.getText(), page=1)


@plugin.route('/search')
def search_type(type, keyword, page):
    dramas, pagination = SearchRequest().get(plugin.getFullPath())
    items = []

    for path, title, poster in dramas:
        item = Drama.get_or_none(Drama.path == path) if type == 'movies' else Drama(title=title, poster=poster)
        items.append((plugin.getUrlFor(path), item if item else Drama.create(**DramaDetailRequest().get(path)), True))

    items.extend(iterate_pagination(pagination))
    plugin.setDirectoryItems(items, 'tvshows') if type == 'movies' else plugin.setDirectoryItems(items)


@plugin.route('/recently-viewed')
def recently_viewed():
    items = []

    for recent_drama in RecentDrama.select(RecentDrama.path).order_by(RecentDrama.timestamp.desc()):
        item = Drama.get_or_none(Drama.path == recent_drama.path)
        item = item if item else Drama.create(**DramaDetailRequest().get(recent_drama.path))
        item.addContextMenuItems([(33100, 'RunPlugin({})'.format(plugin.getUrlFor('/recently-viewed', delete=item.path))),
                                  (33101, 'RunPlugin({})'.format(plugin.getUrlFor('/recently-viewed', delete='%')))])
        items.append((plugin.getUrlFor(item.path), item, True))

    plugin.setDirectoryItems(items, 'tvshows')


@plugin.route('/recently-filtered')
def recently_filtered():
    items = []

    for recent_filter in RecentFilter.select(RecentFilter.path, RecentFilter.title).order_by(RecentFilter.timestamp.desc()):
        recent_filter.addContextMenuItems([(33100, 'RunPlugin({})'.format(plugin.getUrlFor('/recently-filtered', delete=recent_filter.path))),
                                           (33101, 'RunPlugin({})'.format(plugin.getUrlFor('/recently-filtered', delete='%')))])
        items.append((plugin.getUrlFor(recent_filter.path), recent_filter, True))

    plugin.setDirectoryItems(items)


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
    episodes, pagination = RecentlyDramaRequest().get(plugin.getFullPath())
    items = []

    for path, poster, dateadded, title in episodes:
        item = Drama.select().where(Drama.poster == poster).get_or_none()
        item = Drama(title=title, poster=poster, dateadded=dateadded, **({'plot': item.plot} if item else {}))
        item.setProperty('IsPlayable', 'true')
        items.append((plugin.getUrlFor(path), item, False))

    items.extend(iterate_pagination(pagination))
    plugin.setDirectoryItems(items, 'episodes')


@plugin.route('/drama-list')
def drama_category():
    plugin.setDirectoryItems([(plugin.getUrlFor('/category/korean-drama', label=33200), ListItem(33200, iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/category/japanese-drama', label=33201), ListItem(33201, iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/category/taiwanese-drama', label=33202), ListItem(33202, iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/category/hong-kong-drama', label=33203), ListItem(33203, iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/category/chinese-drama', label=33204), ListItem(33204, iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/category/other-asia-drama', label=33205), ListItem(33205, iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/category/thailand-drama', label=33206), ListItem(33206, iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/category/indian-drama', label=33207), ListItem(33207, iconImage='DefaultTVShows.png'), True)])


@plugin.route('/drama-movie')
def movie_category():
    plugin.setDirectoryItems([(plugin.getUrlFor('/category/korean-movies', label=33300), ListItem(33300, iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/category/japanese-movies', label=33301), ListItem(33301, iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/category/taiwanese-movies', label=33302), ListItem(33302, iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/category/hong-kong-movies', label=33303), ListItem(33303, iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/category/chinese-movies', label=33304), ListItem(33304, iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/category/american-movies', label=33305), ListItem(33305, iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/category/other-asia-movies', label=33306), ListItem(33306, iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/category/thailand-movies', label=33307), ListItem(33307, iconImage='DefaultTVShows.png'), True),
                              (plugin.getUrlFor('/category/indian-movies', label=33308), ListItem(33308, iconImage='DefaultTVShows.png'), True)])


@plugin.route('/category/{category}')
@plugin.route('/kshow')
def drama_filter(label, category=None):
    items = Dialog().multiselecttab(getLocalizedString(33400), {
        getLocalizedString(33401): ['#', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S',
                                    'T', 'U', 'V', 'W', 'X', 'Y', 'Z'],
        getLocalizedString(33402): ['Action', 'Adventure', 'Comedy', 'Crime', 'Drama',
                                    'Fantasy', 'Horror', 'Mystery', 'Romance', 'Sci-fi', 'Thriller'],
        getLocalizedString(33403): ['Ongoing', 'Completed', 'Upcoming'],
        getLocalizedString(33404): ['2000', '2001', '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010',
                                    '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022']})

    if items:
        for item in items.values():
            item.sort()

        plugin.redirect(plugin.path, characters=items[getLocalizedString(33401)], genres=items[getLocalizedString(33402)],
                        statuses=items[getLocalizedString(33403)], years=items[getLocalizedString(33404)], label=label)


@plugin.route('/category/{category}')
@plugin.route('/kshow')
def drama_list(label, characters=[], genres=[], statuses=[], years=[], category=None):
    title = ['[' + getLocalizedString(label) + ']']
    expression = Drama.mediatype == plugin.path

    if characters:
        title.append('Character: ' + dumps(characters))
        expression &= reduce(or_, [~(Drama.title % '[a-zA-Z]*') if character == '#' else (Drama.title % (character + '*')) for character in characters])

    if genres:
        title.append('Genre: ' + dumps(genres))
        expression &= Drama.genre % ('*' + '*'.join(genre for genre in genres) + '*')

    if statuses:
        title.append('Status: ' + dumps(statuses))
        expression &= Drama.status << statuses

    if years:
        title.append('Year: ' + dumps(years))
        expression &= Drama.year << years

    RecentFilter.create(path=plugin.getFullPath(), title=' '.join(title))
    items = []

    for item in Drama.select().where(expression):
        items.append((plugin.getUrlFor(item.path), item, True))

    plugin.setDirectoryItems(items, 'tvshows', [SORT_METHOD_TITLE, SORT_METHOD_VIDEO_YEAR])


@plugin.route('/most-popular-drama')
def most_popular_drama(page):
    dramas, pagination = SearchRequest().get(plugin.getFullPath())
    items = []

    for path, title, poster in dramas:
        item = Drama.get_or_none(Drama.path == path)
        item = item if item else Drama(title=title, poster=poster)
        items.append((plugin.getUrlFor(path), item, True))

    items.extend(iterate_pagination(pagination))
    plugin.setDirectoryItems(items, 'tvshows')


@plugin.route('/list-star.html')
def star_list(page):
    stars, pagination = StarListRequest().get(plugin.getFullPath())
    items = []

    for path, title, poster, plot in stars:
        item = Drama(title=title, poster=poster, plot=plot)
        items.append((plugin.getUrlFor(path), item, True))

    items.extend(iterate_pagination(pagination))
    plugin.setDirectoryItems(items)


@plugin.route('/star/{name}')
def star_drama(name):
    dramas = StarDramaRequest().get(plugin.getFullPath())
    items = []

    for path, title, poster in dramas:
        item = Drama.get_or_none(Drama.path == path)
        items.append((plugin.getUrlFor(path), item if item else Drama(title=title, poster=poster), True))

    plugin.setDirectoryItems(items, 'tvshows', [SORT_METHOD_TITLE, SORT_METHOD_VIDEO_YEAR])


@plugin.route('/drama-detail/{name}')
def episode_list(name):
    items = []

    for path, title in EpisodeListRequest().get(plugin.getFullPath()):
        item = Drama(title=title)
        item.setProperty('IsPlayable', 'true')
        items.append((plugin.getUrlFor(path), item, False))

    plugin.setDirectoryItems(items, 'episodes')


@plugin.route('/{name:re("[^.]+.html")}')
def resolve_episode(name):
    title, path, servers = ServerListRequest().get(plugin.getFullPath())
    position = Dialog().select(getLocalizedString(33500),
                               ['[COLOR orange]{}[/COLOR]'.format(name) if scrape_supported(video, '(.+)') else name for video, name in servers])
    item = ListItem(title)
    url = False

    if position != -1:
        executebuiltin('ActivateWindow(busydialognocancel)')
        # if position == 0:
        #     url = resolveurl.resolve(servers[position][0])
        # else:
        url = resolve(servers[position][0])

        if url:
            RecentDrama.create(path=path)
            item.setPath(url)
            subtitle = SubtitleRequest().get(servers[position][0])

            if subtitle:
                item.setSubtitles([subtitle])
        else:
            Dialog().notification(getLocalizedString(33502), '')

        executebuiltin('Dialog.Close(busydialognocancel)')
    else:
        executebuiltin('Playlist.Clear')
        sleep(500)

    plugin.setResolvedUrl(bool(url), item)


def iterate_pagination(pagination):
    localization_code = {'<< First': 33600, '< Previous': 33601, 'Next >': 33602, 'Last >>': 33603}

    for path, title in pagination:
        item = ListItem(localization_code[title], iconImage='DefaultFolderBack.png' if '<' in title else '')
        item.setProperty('SpecialSort', 'bottom')
        yield plugin.getUrlFor(path), item, True


if __name__ == '__main__':
    try:
        ExternalDatabase.connect()
        ExternalDatabase.create()
        InternalDatabase.connect()
        plugin()
    except (ConnectionError, ResolverError) as e:
        Dialog().notification(str(e), '')
    finally:
        ExternalDatabase.close()
        InternalDatabase.close()
        
