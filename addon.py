from bs4 import BeautifulSoup
from requests import Session
from routing import Plugin
from xbmc import Keyboard
from xbmcaddon import Addon
from xbmcgui import Dialog, ListItem

import _strptime
import json
import os
import re
import resolveurl
import shutil
import time
import xbmc
import xbmcplugin


class WatchAsian:
    def __init__(self):
        self._document = None
        self._domain = 'https://www4.watchasian.to'
        self._session = Session()

    def category(self, path):
        response = self._session.get(self._domain + path)
        self._document = BeautifulSoup(response.text, 'html.parser')
        root = self._document.find('div', {'class': 'filter'})
        element = root.find('select', {'id': 'select-genre'})
        genre = [option.text for option in element.find_all('option')]
        select_genre = 0
        element = element.find_next_sibling('select', {'id': 'select-year'})
        year = [option.text for option in element.find_all('option')]
        select_year = 0
        element = element.find_next_sibling('select', {'id': 'select-status'})
        status = [option.text for option in element.find_all('option')]
        select_status = 0
        element = root.find_next_sibling('div')
        block = ['-Select Block-']
        block.extend([div.find('h4').text for div in element.find_all('div', {'class': 'list-content'})])
        select_block = 0

        while True:
            items = [block[select_block], genre[select_genre], year[select_year], status[select_status]]
            position = Dialog().select('Filter', items)

            if position == 0:
                select_block = max(Dialog().select('Genre', block), 0)
            elif position == 1:
                select_genre = max(Dialog().select('Genre', genre), 0)
            elif position == 2:
                select_year = max(Dialog().select('Year', year), 0)
            elif position == 3:
                select_status = max(Dialog().select('Status', status), 0)
            else:
                break

        block = None if select_block == 0 else block[select_block]
        genre = None if select_genre == 0 else genre[select_genre]
        year = None if select_year == 0 else 'year_' + year[select_year]
        status = None if select_status == 0 else 'status_' + status[select_status]
        root = root.find_next_sibling()
        items = []

        for element in root.find_all('div', {'class': 'list-content'}):
            if block is None or element.find('h4').text == block:
                for li in element.find_all('li'):
                    if genre is not None and genre not in json.loads(li.attrs['data-genre']):
                        continue

                    if year is not None and year not in li.attrs['class']:
                        continue

                    if status is not None and status not in li.attrs['class']:
                        continue

                    href = li.find('a').attrs['href']
                    info = self.drama_detail_info(href)
                    item = ListItem(info['video']['title'])
                    item.setArt({'poster': info['poster']})
                    item.setInfo('video', info['video'])
                    items.append((plugin.url_for_path(href), item, True))

        xbmcplugin.setContent(plugin.handle, 'videos')
        xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
        xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_GENRE)
        xbmcplugin.endOfDirectory(plugin.handle)

    def drama_detail(self, path):
        info = self.drama_detail_info(path)
        root = self._document.find('ul', {'class': 'list-episode-item-2 all-episode'})
        items = []

        for li in root.find_all('li'):
            title = '[' + li.find('span').text + '] ' + li.find('h3').text.replace('\n', '').strip()
            href = '/episode-detail' + li.find('a').attrs['href']
            info['video']['title'] = title

            item = ListItem(title)
            item.setArt({'poster': info['poster']})
            item.setInfo('video', info['video'])
            item.setProperty('IsPlayable', 'true')
            items.append((plugin.url_for_path(href), item, False))

        xbmcplugin.setPluginCategory(plugin.handle, info['video']['title'])
        xbmcplugin.setContent(plugin.handle, 'videos')
        xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
        xbmcplugin.endOfDirectory(plugin.handle)

    def drama_detail_info(self, path):
        response = self._session.get(self._domain + path)
        self._document = BeautifulSoup(response.text, 'html.parser')
        root = self._document.find('div', {'class': 'info'})
        poster = root.find_previous().attrs['src']
        director = root.find('span', text='Director:')
        year = root.find('span', text='Released:')
        aired = root.find('span', text='Airs:')
        video = {
            'title': root.find('h1').text.strip(),
            'plot': root.find('span', text='Description').find_next().text,
            'director': '' if director is None else director.next_sibling.strip(),
            'country': str(root.find('span', text='Country: ').next_sibling),
            'status': root.find('span', text='Status:').find_next().text,
            'year': '' if year is None else year.find_next().text,
            'genre': [a.text for a in root.find('span', text='Genre:').find_next_siblings()],
            'aired': '' if aired is None else time.strftime('%Y-%m-%d',
                                                            _strptime._strptime_time(str(aired.next_sibling),
                                                                                     ' %b %d, %Y'))
        }
        return {'poster': poster, 'video': video}

    def drama_pagination(self, path, query):
        response = self._session.get(self._domain + path + query, headers={'referer': self._domain})
        self._document = BeautifulSoup(response.text, 'html.parser')
        root = self._document.find('ul', {'class': 'switch-block list-episode-item'})
        items = []

        if root is not None:
            for li in root.find_all('li'):
                href = li.find('a').attrs['href']
                info = self.drama_detail_info(href)
                item = ListItem(info['video']['title'])
                item.setArt({'poster': info['poster']})
                item.setInfo('video', info['video'])
                items.append((plugin.url_for_path(href), item, True))

            root = root.find_next_sibling()

            if root is not None:
                for li in root.find_all('li', {'class': ['next', 'previous']}):
                    title = '[B]' + li.text + '[/B]'
                    href = path + li.find('a').attrs['href']
                    item = ListItem(title)
                    item.setProperty('SpecialSort', 'bottom')
                    items.append((plugin.url_for_path(href), item, True))

        xbmcplugin.setContent(plugin.handle, 'videos')
        xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
        xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_GENRE)
        xbmcplugin.endOfDirectory(plugin.handle)

    def episode_pagination(self, path, query):
        response = self._session.get(self._domain + path + query)
        self._document = BeautifulSoup(response.text, 'html.parser')
        root = self._document.find('ul', {'class': 'switch-block list-episode-item'})
        items = []

        if root is not None:
            for li in root.find_all('li'):
                title = '[' + li.find('span').text + '] ' + li.find('a').attrs['title']
                poster = li.find('img').attrs['data-original']
                href = '/episode-detail' + li.find('a').attrs['href']
                item = ListItem(title)
                item.setArt({'poster': poster})
                item.setInfo('video', {})
                item.setProperty('IsPlayable', 'true')
                items.append((plugin.url_for_path(href), item, False))

            root = root.find_next_sibling()

            if root is not None:
                for li in root.find_all('li', {'class': ['next', 'previous']}):
                    title = '[B]' + li.text + '[/B]'
                    href = path + li.find('a').attrs['href']
                    item = ListItem(title)
                    items.append((plugin.url_for_path(href), item, True))

        xbmcplugin.setContent(plugin.handle, 'videos')
        xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
        xbmcplugin.endOfDirectory(plugin.handle)

    def play_episode(self, path):
        response = self._session.get(self._domain + path)
        self._document = BeautifulSoup(response.text, 'html.parser')
        root = self._document.find('div', {'class': 'block watch-drama'}).find('h1')
        items = []

        for li in root.find_next_sibling('div', {'class': 'anime_muti_link'}).find_all('li'):
            item = ListItem(li.next.title(), path=re.sub('^//', 'https://', li.attrs['data-video']))
            items.append(item)

        position = Dialog().select('Choose Server', items)

        if position != -1:
            xbmc.executebuiltin("ActivateWindow(busydialog)")
            plugin_dirs = os.path.join(Addon().getAddonInfo('path'), 'resources/lib/resolveurl/plugins')
            resolveurl.add_plugin_dirs(plugin_dirs)
            url = resolveurl.resolve(items[position].getPath())

            if url:
                item = ListItem(root.text.strip(), path=url)
                xbmcplugin.setResolvedUrl(plugin.handle, True, item)
            else:
                Dialog().notification('Couldn\'t Resolve Server', '')


dramacool = WatchAsian()
plugin = Plugin()
shutil.rmtree(xbmc.translatePath(Addon().getAddonInfo('profile')), ignore_errors=True)


@plugin.route('/')
def index():
    xbmcplugin.setPluginCategory(plugin.handle, 'Categories')
    xbmcplugin.setContent(plugin.handle, 'videos')
    items = [(plugin.url_for_path('/search?type=movies&page=1'), ListItem('Search'), True),
             (plugin.url_for_path('/recently-added?page=1'), ListItem('Recently Added Drama'), True),
             (plugin.url_for_path('/recently-added-movie?page=1'), ListItem('Recently Added Movie'), True),
             (plugin.url_for_path('/recently-added-kshow?page=1'), ListItem('Recently Added Korean Show'), True),
             (plugin.url_for_path('/most-popular-drama?page=1'), ListItem('Popular Drama'), True),
             (plugin.url_for_path('/kshow'), ListItem('Korean Show'), True),
             (plugin.url_for_path('/category/korean-drama'), ListItem('Korean Drama'), True),
             (plugin.url_for_path('/category/japanese-drama'), ListItem('Japanese Drama'), True),
             (plugin.url_for_path('/category/taiwanese-drama'), ListItem('Taiwanese Drama'), True),
             (plugin.url_for_path('/category/hong-kong-drama'), ListItem('Hong Kong Drama'), True),
             (plugin.url_for_path('/category/chinese-drama'), ListItem('Chinese Drama'), True),
             (plugin.url_for_path('/category/american-drama'), ListItem('American Drama'), True),
             (plugin.url_for_path('/category/other-asia-drama'), ListItem('Other Asia Drama'), True),
             (plugin.url_for_path('/category/thailand-drama'), ListItem('Thailand Drama'), True),
             (plugin.url_for_path('/category/philippine-drama'), ListItem('Philippine Drama'), True),
             (plugin.url_for_path('/category/korean-movies'), ListItem('Korean Movies'), True),
             (plugin.url_for_path('/category/japanese-movies'), ListItem('Japanese Movies'), True),
             (plugin.url_for_path('/category/taiwanese-movies'), ListItem('Taiwanese Movies'), True),
             (plugin.url_for_path('/category/hong-kong-movies'), ListItem('Hong Kong Movies'), True),
             (plugin.url_for_path('/category/chinese-movies'), ListItem('Chinese Movies'), True),
             (plugin.url_for_path('/category/american-movies'), ListItem('American Movies'), True),
             (plugin.url_for_path('/category/other-asia-movies'), ListItem('Other Asia Movies'), True),
             (plugin.url_for_path('/category/thailand-movies'), ListItem('Thailand Movies'), True),
             (plugin.url_for_path('/category/philippine-movies'), ListItem('Philippine Movies'), True)]
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/search')
def search():
    if 'keyword' in plugin.args:
        keyword = plugin.args['keyword'][0]
    else:
        keyboard = Keyboard()
        keyboard.doModal()

        if keyboard.isConfirmed():
            keyword = keyboard.getText()
        else:
            return

    xbmcplugin.setPluginCategory(plugin.handle, 'Search "' + keyword + '"')
    dramacool.drama_pagination('/search', '?type=movies&keyword=' + keyword + '&page=' + plugin.args['page'][0])


@plugin.route('/recently-added')
def recently_added():
    xbmcplugin.setPluginCategory(plugin.handle, 'Recently Added Drama')
    dramacool.episode_pagination('/recently-added', '?page=' + plugin.args['page'][0])


@plugin.route('/recently-added-movie')
def recently_added_movie():
    xbmcplugin.setPluginCategory(plugin.handle, 'Recently Added Movie')
    dramacool.episode_pagination('/recently-added-movie', '?page=' + plugin.args['page'][0])


@plugin.route('/recently-added-kshow')
def recently_added_kshow():
    xbmcplugin.setPluginCategory(plugin.handle, 'Recently Added Korean Show')
    dramacool.episode_pagination('/recently-added-kshow', '?page=' + plugin.args['page'][0])


@plugin.route('/most-popular-drama')
def most_popular_drama():
    xbmcplugin.setPluginCategory(plugin.handle, 'Popular Drama')
    dramacool.drama_pagination('/most-popular-drama', '?page=' + plugin.args['page'][0])


@plugin.route('/category/<category_id>')
def category(category_id):
    xbmcplugin.setPluginCategory(plugin.handle, category_id.replace('-', ' ').title())
    dramacool.category('/category/' + category_id)


@plugin.route('/kshow')
def kshow():
    xbmcplugin.setPluginCategory(plugin.handle, 'Korean Show')
    dramacool.category('/kshow')


@plugin.route('/drama-detail/<drama_id>')
def drama_detail(drama_id):
    dramacool.drama_detail('/drama-detail/' + drama_id)


@plugin.route('/episode-detail/<episode_id>')
def episode_detail(episode_id):
    dramacool.play_episode('/' + episode_id)


if __name__ == '__main__':
    plugin.run()
