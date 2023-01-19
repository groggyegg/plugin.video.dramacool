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
from request import (RecentlyDramaRequest, SearchRequest, StarListRequest, StarDramaRequest,
                     DramaDetailRequest, EpisodeListRequest, ServerListRequest, SubtitleRequest)

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
        (plugin.getSerializedUrlFor('/drama-list'), ListItem(getLocalizedString(33006), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/drama-movie'), ListItem(getLocalizedString(33007), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/kshow', label=33008), ListItem(getLocalizedString(33008), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/most-popular-drama', page=1), ListItem(getLocalizedString(33009), iconImage='DefaultFavourites.png'), True),
        (plugin.getSerializedUrlFor('/list-star.html', page=1), ListItem(getLocalizedString(33010), iconImage='DefaultFavourites.png'), True)
    ])
    plugin.endOfDirectory()


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
        items.append((plugin.getSerializedUrlFor(path), item if item else Drama.create(**DramaDetailRequest().get(path)), True))

    items.extend(iterate_pagination(pagination))

    if type == 'movies':
        plugin.setContent('tvshows')

    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/recently-viewed')
def recently_viewed():
    items = []

    for recent_drama in RecentDrama.select(RecentDrama.path).order_by(RecentDrama.timestamp.desc()):
        item = Drama.get_or_none(Drama.path == recent_drama.path)
        item = item if item else Drama.create(**DramaDetailRequest().get(recent_drama.path))
        item.addContextMenuItems([
            (getLocalizedString(33100), 'RunPlugin({})'.format(plugin.getSerializedUrlFor('/recently-viewed', delete=item.path))),
            (getLocalizedString(33101), 'RunPlugin({})'.format(plugin.getSerializedUrlFor('/recently-viewed', delete='%')))
        ])
        items.append((plugin.getUrlFor(item.path), item, True))

    plugin.setContent('tvshows')
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/recently-filtered')
def recently_filtered():
    items = []

    for recent_filter in RecentFilter.select(RecentFilter.path, RecentFilter.title).order_by(RecentFilter.timestamp.desc()):
        recent_filter.addContextMenuItems([
            (getLocalizedString(33100), 'RunPlugin({})'.format(plugin.getSerializedUrlFor('/recently-filtered', delete=recent_filter.path))),
            (getLocalizedString(33101), 'RunPlugin({})'.format(plugin.getSerializedUrlFor('/recently-filtered', delete='%')))
        ])
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
    episodes, pagination = RecentlyDramaRequest().get(plugin.getFullPath())
    items = []

    for path, poster, dateadded, title in episodes:
        item = Drama.select().where(Drama.poster == poster).get_or_none()
        plot = item.plot if item else None
        item = Drama(title=title, poster=poster, plot=plot)
        item.setProperty('IsPlayable', 'true')
        items.append((plugin.getSerializedUrlFor(path), item, False))

    items.extend(iterate_pagination(pagination))
    plugin.setContent('episodes')
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/drama-list')
def drama_category():
    plugin.addDirectoryItems([
        (plugin.getSerializedUrlFor('/category/korean-drama', label=33200), ListItem(getLocalizedString(33200), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/japanese-drama', label=33201), ListItem(getLocalizedString(33201), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/taiwanese-drama', label=33202), ListItem(getLocalizedString(33202), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/hong-kong-drama', label=33203), ListItem(getLocalizedString(33203), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/chinese-drama', label=33204), ListItem(getLocalizedString(33204), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/other-asia-drama', label=33205), ListItem(getLocalizedString(33205), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/thailand-drama', label=33206), ListItem(getLocalizedString(33206), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/indian-drama', label=33207), ListItem(getLocalizedString(33207), iconImage='DefaultTVShows.png'), True)
    ])
    plugin.endOfDirectory()


@plugin.route('/drama-movie')
def movie_category():
    plugin.addDirectoryItems([
        (plugin.getSerializedUrlFor('/category/korean-movies', label=33300), ListItem(getLocalizedString(33300), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/japanese-movies', label=33301), ListItem(getLocalizedString(33301), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/taiwanese-movies', label=33302), ListItem(getLocalizedString(33302), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/hong-kong-movies', label=33303), ListItem(getLocalizedString(33303), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/chinese-movies', label=33304), ListItem(getLocalizedString(33304), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/american-movies', label=33305), ListItem(getLocalizedString(33305), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/other-asia-movies', label=33306), ListItem(getLocalizedString(33306), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/thailand-movies', label=33307), ListItem(getLocalizedString(33307), iconImage='DefaultTVShows.png'), True),
        (plugin.getSerializedUrlFor('/category/indian-movies', label=33308), ListItem(getLocalizedString(33308), iconImage='DefaultTVShows.png'), True)
    ])
    plugin.endOfDirectory()


@plugin.route('/category/{}')
@plugin.route('/kshow')
def drama_filter(label):
    items = Dialog().multiselecttab(getLocalizedString(33400), {
        getLocalizedString(33401): ['#', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S',
                                    'T', 'U', 'V', 'W', 'X', 'Y', 'Z'],
        getLocalizedString(33402): ['Action', 'Adventure', 'Comedy', 'Crime', 'Drama',
                                    'Fantasy', 'Horror', 'Mystery', 'Romance', 'Sci-fi', 'Thriller'],
        getLocalizedString(33403): ['Ongoing', 'Completed', 'Upcoming'],
        getLocalizedString(33404): ['2000', '2001', '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011',
                                    '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023']})

    if items:
        for item in items.values():
            item.sort()

        plugin.redirect(plugin.path, characters=items[getLocalizedString(33401)], genres=items[getLocalizedString(33402)],
                        statuses=items[getLocalizedString(33403)], years=items[getLocalizedString(33404)], label=label)


@plugin.route('/category/{}')
@plugin.route('/kshow')
def drama_list(label, characters=[], genres=[], statuses=[], years=[]):
    title = ['[{}]'.format(getLocalizedString(label))]
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

    RecentFilter.create(path=plugin.getSerializedFullPath(), title=' '.join(title))
    items = []

    for item in Drama.select().where(expression):
        items.append((plugin.getSerializedUrlFor(item.path), item, True))

    plugin.addSortMethods(SortMethod.TITLE, SortMethod.VIDEO_YEAR)
    plugin.setContent('tvshows')
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/most-popular-drama')
def most_popular_drama(page):
    dramas, pagination = SearchRequest().get(plugin.getFullPath())
    items = []

    for path, title, poster in dramas:
        item = Drama.get_or_none(Drama.path == path)
        item = item if item else Drama(title=title, poster=poster)
        items.append((plugin.getSerializedUrlFor(path), item, True))

    items.extend(iterate_pagination(pagination))
    plugin.setContent('tvshows')
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/list-star.html')
def star_list(page):
    stars, pagination = StarListRequest().get(plugin.getFullPath())
    items = []

    for path, title, poster, plot in stars:
        item = Drama(title=title, poster=poster, plot=plot)
        items.append((plugin.getSerializedUrlFor(path), item, True))

    items.extend(iterate_pagination(pagination))
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/star/{}')
def star_drama():
    dramas = StarDramaRequest().get(plugin.getFullPath())
    items = []

    for path, title, poster in dramas:
        item = Drama.get_or_none(Drama.path == path)
        items.append((plugin.getSerializedUrlFor(path), item if item else Drama(title=title, poster=poster), True))

    plugin.addSortMethods(SortMethod.TITLE, SortMethod.VIDEO_YEAR)
    plugin.setContent('tvshows')
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory()


@plugin.route('/drama-detail/{}')
def episode_list():
    items = []

    for path, title in EpisodeListRequest().get(plugin.getFullPath()):
        item = Drama(title=title)
        item.setProperty('IsPlayable', 'true')
        items.append((plugin.getSerializedUrlFor(path), item, False))

    plugin.setContent('episodes')
    plugin.addDirectoryItems(items)
    plugin.endOfDirectory(cacheToDisc=False)


@plugin.route('/{:re("[^.]+.html")}')
def resolve_episode():
    title, path, servers = ServerListRequest().get(plugin.getFullPath())
    position = Dialog().select(getLocalizedString(33500), ['[COLOR orange]{}[/COLOR]'.format(name) if scrape_supported(video, '(.+)') else name
                                                           for video, name in servers])
    item = ListItem(title)
    url = False

    if position != -1:
        executebuiltin('ActivateWindow(busydialognocancel)')
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
    localization_code = {'<< First': getLocalizedString(33600),
                         '< Previous': getLocalizedString(33601),
                         'Next >': getLocalizedString(33602),
                         'Last >>': getLocalizedString(33603)}

    for path, title in pagination:
        item = ListItem(localization_code[title], iconImage='DefaultFolderBack.png' if '<' in title else '')
        item.setProperty('SpecialSort', 'bottom')
        yield plugin.getSerializedUrlFor(path), item, True


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
