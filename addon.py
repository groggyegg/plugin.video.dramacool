from bs4 import BeautifulSoup
from requests import Session
from routing import Plugin
from sqlite3 import Row
from xbmc import Keyboard
from xbmcaddon import Addon
from xbmcgui import Dialog, ListItem

import base64
import os
import re
import resolveurl
import sqlite3
import sys
import xbmc
import xbmcplugin

addon_path = Addon().getAddonInfo('path')
database = '{}/{}'.format(xbmc.translatePath(addon_path), 'resources/data/dramacool.db')
connection = sqlite3.connect(database)
cursor = connection.cursor()
domains = ('https://watchasian.net', 'https://www3.dramacool.movie')
plugin = Plugin()
session = Session()


@plugin.route('/')
def index():
    items = [(plugin.url_for_path('/search?type=movies&page=1'), ListItem('Search Drama'), True),
             (plugin.url_for_path('/recently-viewed'), ListItem('Recently Viewed'), True),
             (plugin.url_for_path('/recently-added?page=1'), ListItem('Recently Added Drama'), True),
             (plugin.url_for_path('/recently-added-movie?page=1'), ListItem('Recently Added Movie'), True),
             (plugin.url_for_path('/recently-added-kshow?page=1'), ListItem('Recently Added KShow'), True),
             (plugin.url_for_path('/navbar/drama-list'), ListItem('Drama List'), True),
             (plugin.url_for_path('/navbar'), ListItem('Drama Movie'), True),
             (plugin.url_for_path('/kshow'), ListItem('KShow'), True),
             (plugin.url_for_path('/most-popular-drama'), ListItem('Popular Drama'), True)]

    xbmcplugin.setContent(plugin.handle, 'videos')
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/recently-viewed')
def recently_viewed():
    if 'delete' in plugin.args:
        cursor.execute('DELETE FROM recently_viewed WHERE path = ?', (base64.b64decode(plugin.args['delete'][0]),))
        xbmc.executebuiltin('Container.Refresh')
        return

    cursor.execute('SELECT path FROM recently_viewed ORDER BY last_visited DESC')
    items = []

    for (path,) in cursor.fetchall():
        drama = drama_detail(path)
        item = ListItem(drama['title'])
        item.addContextMenuItems([('Remove', 'RunPlugin(plugin://plugin.video.dramacool/recently-viewed?delete={})'.format(base64.b64encode(path)))])
        item.setArt({'poster': drama.pop('poster')})
        item.setInfo('video', drama)
        items.append((plugin.url_for_path(path), item, True))

    xbmcplugin.setContent(plugin.handle, 'videos')
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/most-popular-drama')
@plugin.route('/recently-added')
@plugin.route('/recently-added-movie')
@plugin.route('/recently-added-kshow')
@plugin.route('/search')
def pagination():
    if plugin.path == '/search' and 'keyword' not in plugin.args:
        keyboard = Keyboard()
        keyboard.doModal()

        if keyboard.isConfirmed():
            response = request('{}{}&keyword={}'.format(plugin.path, sys.argv[2], keyboard.getText()))
        else:
            return
    else:
        response = request(plugin.path)

    document = BeautifulSoup(response.text, 'html.parser').find('ul', {'class': 'switch-block list-episode-item'})
    items = []

    if document is not None:
        if plugin.path in ('/most-popular-drama', '/search'):
            for a in document.find_all('a'):
                path = a.attrs['href']
                drama = drama_detail(path)
                item = ListItem(drama['title'])
                item.setArt({'poster': drama.pop('poster')})
                item.setInfo('video', drama)
                items.append((plugin.url_for_path(path), item, True))
        else:
            for a in document.find_all('a'):
                item = ListItem(u'[{}] {}'.format(a.find('span', {'class': 'type'}).text, a.attrs['title']))
                item.setArt({'poster': a.find('img').attrs['data-original']})
                item.setInfo('video', {})
                item.setProperty('IsPlayable', 'true')
                items.append((plugin.url_for_path('/play{}'.format(a.attrs['href'])), item, False))

        document = document.find_next_sibling()

        if document is not None:
            for li in document.find_all('li', {'class': ['next', 'previous']}):
                item = ListItem(li.text)
                items.append((plugin.url_for_path(plugin.path + li.find('a').attrs['href']), item, True))

    xbmcplugin.setContent(plugin.handle, 'videos')
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/navbar/drama-list')
@plugin.route('/navbar')
def navbar():
    if plugin.path == '/navbar/drama-list':
        items = [(plugin.url_for_path('/category/korean-drama'), ListItem('Korean Drama'), True),
                 (plugin.url_for_path('/category/japanese-drama'), ListItem('Japanese Drama'), True),
                 (plugin.url_for_path('/category/taiwanese-drama'), ListItem('Taiwanese Drama'), True),
                 (plugin.url_for_path('/category/hong-kong-drama'), ListItem('Hong Kong Drama'), True),
                 (plugin.url_for_path('/category/chinese-drama'), ListItem('Chinese Drama'), True),
                 (plugin.url_for_path('/category/other-asia-drama'), ListItem('Other Asia Drama'), True),
                 (plugin.url_for_path('/category/thailand-drama'), ListItem('Thailand Drama'), True)]
    else:
        items = [(plugin.url_for_path('/category/korean-movies'), ListItem('Korean Movies'), True),
                 (plugin.url_for_path('/category/japanese-movies'), ListItem('Japanese Movies'), True),
                 (plugin.url_for_path('/category/taiwanese-movies'), ListItem('Taiwanese Movies'), True),
                 (plugin.url_for_path('/category/hong-kong-movies'), ListItem('Hong Kong Movies'), True),
                 (plugin.url_for_path('/category/chinese-movies'), ListItem('Chinese Movies'), True),
                 (plugin.url_for_path('/category/american-movies'), ListItem('American Movies'), True),
                 (plugin.url_for_path('/category/other-asia-movies'), ListItem('Other Asia Movies'), True),
                 (plugin.url_for_path('/category/thailand-movies'), ListItem('Thailand Movies'), True)]

    xbmcplugin.setContent(plugin.handle, 'videos')
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/category/korean-drama')
@plugin.route('/category/japanese-drama')
@plugin.route('/category/taiwanese-drama')
@plugin.route('/category/hong-kong-drama')
@plugin.route('/category/chinese-drama')
@plugin.route('/category/other-asia-drama')
@plugin.route('/category/thailand-drama')
@plugin.route('/category/korean-movies')
@plugin.route('/category/japanese-movies')
@plugin.route('/category/taiwanese-movies')
@plugin.route('/category/hong-kong-movies')
@plugin.route('/category/chinese-movies')
@plugin.route('/category/american-movies')
@plugin.route('/category/other-asia-movies')
@plugin.route('/category/thailand-movies')
@plugin.route('/kshow')
def filter_category():
    path = base64.b64encode(plugin.path.encode())
    items = [(plugin.url_for_path('/filter/{}/char'.format(path)), ListItem('Filter By Char'), True),
             (plugin.url_for_path('/filter/{}/year'.format(path)), ListItem('Filter By Year'), True),
             (plugin.url_for_path('/filter/{}/status'.format(path)), ListItem('Filter By Status'), True)]

    xbmcplugin.setContent(plugin.handle, 'videos')
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/filter/<path>/<filter_id>')
def filter_content(path, filter_id):
    response = request(base64.b64decode(path))
    document = BeautifulSoup(response.text, 'html.parser')
    items = []

    if filter_id == 'char':
        for div in document.find_all('div', {'class': 'list-content'}):
            title = div.find('h4').text
            item = ListItem(title)
            items.append((plugin.url_for_path('{}/{}'.format(plugin.path, ord(title))), item, True))
    else:
        for option in document.find('select', {'id': 'select-{}'.format(filter_id)}).find_all('option')[1:]:
            item = ListItem(option.text)
            items.append((plugin.url_for_path('{}/{}'.format(plugin.path, option.attrs['value'])), item, True))

    xbmcplugin.setContent(plugin.handle, 'videos')
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/filter/<path>/<filter_id>/<select_id>')
def list_content(path, filter_id, select_id):
    response = request(base64.b64decode(path))
    document = BeautifulSoup(response.text, 'html.parser')
    items = []

    if filter_id == 'char':
        select_id = chr(int(select_id))

        for div in document.find_all('div', {'class': 'list-content'}):
            if div.find('h4').text == select_id:
                for a in div.find('ul', {'class': 'filter-char'}).find_all('a'):
                    path = a.attrs['href']
                    drama = drama_detail(path)
                    item = ListItem(drama['title'])
                    item.setArt({'poster': drama.pop('poster')})
                    item.setInfo('video', drama)
                    items.append((plugin.url_for_path(path), item, True))

                break
    else:
        for li in document.find_all('li', {'class': '{}_{}'.format(filter_id, select_id)}):
            path = li.find('a').attrs['href']
            drama = drama_detail(path)
            item = ListItem(drama['title'])
            item.setArt({'poster': drama.pop('poster')})
            item.setInfo('video', drama)
            items.append((plugin.url_for_path(path), item, True))

    xbmcplugin.setContent(plugin.handle, 'videos')
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/drama-detail/<path>')
def list_episode(path):
    path = '/drama-detail/{}'.format(path)
    response = request(path)
    document = BeautifulSoup(response.text, 'html.parser')
    cursor.execute('INSERT INTO recently_viewed (path) VALUES (?)', (path,))
    items = []

    for a in document.find('ul', {'class': 'all-episode'}).find_all('a'):
        item = ListItem('[{}] {}'.format(a.find('span').text, a.find('h3').text.strip('\n ')))
        item.setInfo('video', {})
        item.setProperty('IsPlayable', 'true')
        items.append((plugin.url_for_path('/play{}'.format(a.attrs['href'])), item, False))

    xbmcplugin.setContent(plugin.handle, 'videos')
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/play/<path>')
def play_episode(path):
    response = request('/{}'.format(path))
    document = BeautifulSoup(response.text, 'html.parser')
    title = document.find('h1').text.strip()
    all_server = document.find_all('li', {'data-video': True})
    position = Dialog().select('Choose Server', [server.contents[0] for server in all_server])

    if position != -1:
        xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
        resolveurl.add_plugin_dirs(os.path.join(addon_path, 'resources/lib/resolveurl/plugins'))
        url = resolveurl.resolve(all_server[position].attrs['data-video'])

        if url:
            item = ListItem(title, path=url)
            sub = re.search('&sub=([^&]+)', all_server[position].attrs['data-video'])

            if sub:
                response = session.get('https://embed.watchasian.to/player/sub/index.php?id=' + sub.group(1))
                file = os.path.join(addon_path, 'resources/data/dramacool.en.srt')
                item.setSubtitles([file])

                with open(file, 'w') as o:
                    for i, text in enumerate(re.split('WEBVTT\r\n\r\n|\r\n\r\n', response.text)[1:], start=1):
                        o.write('{}\r\n{}\r\n\r\n'.format(i, text.encode('utf-8')))

            xbmc.executebuiltin('Dialog.Close(busydialognocancel)')
            xbmcplugin.setResolvedUrl(plugin.handle, True, item)
        else:
            xbmc.executebuiltin('Dialog.Close(busydialognocancel)')
            Dialog().notification('Couldn\'t Resolve Server', '')


def drama_detail(path):
    cursor.row_factory = Row
    cursor.execute('SELECT * FROM drama WHERE path = ?', (path,))
    drama = cursor.fetchone()

    if drama is None:
        response = request(path)
        document = BeautifulSoup(response.content, 'html.parser')
        element = document.find('div', {'class': 'details'})
        director = element.find('span', text='Director:')
        year = document.find('span', text='Released:').find_next_sibling('a').text
        cast = document.find('div', {'class': 'slider-star'})
        drama = {
            'poster': element.find('img').attrs['src'],
            'title': element.find('h1').text,
            'plot': element.find('span', text='Description').parent.find_next_sibling().text,
            'country': document.find('span', text='Country: ').next_sibling.strip(),
            'status': document.find('span', text='Status:').find_next_sibling('a').text,
            'genre': [a.text for a in document.find('span', text='Genre:').find_next_siblings('a')],
            'director': None if director is None else director.next_sibling.strip(),
            'year': int(year) if year.isdigit() else None,
            'cast': [] if cast is None else [a.attrs['title'] for a in cast.find_all('a')]
        }
        cursor.execute('INSERT INTO drama VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (
            path,
            drama['poster'],
            drama['title'],
            drama['plot'],
            drama['director'],
            drama['country'],
            drama['status'],
            drama['year']
        ))

        for label in drama['genre']:
            cursor.execute('INSERT INTO genre VALUES (?, ?)', (path, label))

        for name in drama['cast']:
            cursor.execute('INSERT INTO cast VALUES (?, ?)', (path, name))
    else:
        drama = dict(drama)
        cursor.row_factory = None
        cursor.execute('SELECT name FROM cast WHERE path = ?', (path,))
        drama['cast'] = [name for (name,) in cursor.fetchall()]
        cursor.execute('SELECT label FROM genre WHERE path = ?', (path,))
        drama['genre'] = [label for (label,) in cursor.fetchall()]

    return drama


def request(path):
    for domain in domains:
        response = session.get(domain + path)

        if response.status_code == 200:
            return response


def create_database():
    cursor.execute('CREATE TABLE IF NOT EXISTS recently_viewed ('
                   + 'path TEXT UNIQUE ON CONFLICT REPLACE, '
                   + 'last_visited DATETIME DEFAULT CURRENT_TIMESTAMP)')
    cursor.execute('CREATE TABLE IF NOT EXISTS drama ('
                   + 'path TEXT PRIMARY KEY ON CONFLICT IGNORE, '
                   + 'poster TEXT, '
                   + 'title TEXT NOT NULL, '
                   + 'plot TEXT, '
                   + 'director TEXT, '
                   + 'country TEXT, '
                   + 'status TEXT, '
                   + 'year SMALLINT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS cast ('
                   + 'path TEXT NOT NULL, '
                   + 'name TEXT NOT NULL, '
                   + 'PRIMARY KEY (path, name) ON CONFLICT IGNORE)')
    cursor.execute('CREATE TABLE IF NOT EXISTS genre ('
                   + 'path TEXT NOT NULL, '
                   + 'label TEXT NOT NULL, '
                   + 'PRIMARY KEY (path, label) ON CONFLICT IGNORE)')

    for path in ['/drama-list', '/kshow']:
        response = request(path)
        document = BeautifulSoup(response.content, 'html.parser')

        for li in document.find_all('li', {'class': 'filter-item'}):
            drama_detail(li.find('a').attrs['href'])


if __name__ == '__main__':
    plugin.run()

connection.commit()
connection.close()
