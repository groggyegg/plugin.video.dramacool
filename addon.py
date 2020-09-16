from bs4 import BeautifulSoup
from requests import Session
from rerouting import Rerouting
from resources.lib.database import ExternalDatabase, InternalDatabase
from xbmc import Keyboard
from xbmcaddon import Addon
from xbmcgui import Dialog, ListItem

import os
import re
import resolveurl
import xbmc
import xbmcplugin

__plugins__ = os.path.join(xbmc.translatePath(Addon().getAddonInfo('path')), 'resources/lib/resolveurl/plugins')
__temp__ = os.path.join(xbmc.translatePath(Addon().getAddonInfo('path')), 'resources/data/temp')

domains = ('https://watchasian.net', 'https://www3.dramacool.movie')
localized_str = Addon().getLocalizedString
plugin = Rerouting()
session = Session()


@plugin.route('/')
def index():
    items = [(plugin.url_for('/search?type=movies&page=1'), ListItem(localized_str(33000)), True),
             (plugin.url_for('/search?type=stars&page=1'), ListItem(localized_str(33001)), True),
             (plugin.url_for('/recently-viewed'), ListItem(localized_str(33002)), True),
             (plugin.url_for('/recently-added?page=1'), ListItem(localized_str(33003)), True),
             (plugin.url_for('/recently-added-movie?page=1'), ListItem(localized_str(33004)), True),
             (plugin.url_for('/recently-added-kshow?page=1'), ListItem(localized_str(33005)), True),
             (plugin.url_for('/drama-list'), ListItem(localized_str(33006)), True),
             (plugin.url_for('/drama-movie'), ListItem(localized_str(33007)), True),
             (plugin.url_for('/filter-select/kshow'), ListItem(localized_str(33008)), True),
             (plugin.url_for('/most-popular-drama?page=1'), ListItem(localized_str(33009)), True),
             (plugin.url_for('/list-star.html?page=1'), ListItem(localized_str(33010)), True)]

    xbmcplugin.setContent(plugin.handle, 'videos')
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route(r'/recently-viewed(\?delete=(?P<delete>[^&]+))?')
def recently_viewed(delete=None):
    ExternalDatabase.connect()
    InternalDatabase.connect()

    if delete is not None:
        ExternalDatabase.remove(delete)
        xbmc.executebuiltin('Container.Refresh')
    else:
        items = []

        for path in ExternalDatabase.fetchall():
            drama = drama_detail(path)
            item = ListItem(drama['title'])
            item.addContextMenuItems([
                (localized_str(33100), 'RunPlugin(plugin://plugin.video.dramacool/recently-viewed?delete=' + path + ')'),
                (localized_str(33101), 'RunPlugin(plugin://plugin.video.dramacool/recently-viewed?delete=%)')
            ])
            item.setArt({'poster': drama.pop('poster')})
            item.setInfo('video', drama)
            items.append((plugin.url_for(path), item, True))

        xbmcplugin.setContent(plugin.handle, 'videos')
        xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
        xbmcplugin.endOfDirectory(plugin.handle)

    ExternalDatabase.close()
    InternalDatabase.close()


@plugin.route(r'/list-star.html\?page=[^&]+')
@plugin.route(r'/most-popular-drama\?page=[^&]+')
@plugin.route(r'/recently-added\?page=[^&]+')
@plugin.route(r'/recently-added-movie\?page=[^&]+')
@plugin.route(r'/recently-added-kshow\?page=[^&]+')
@plugin.route(r'/search\?((type=movies|type=stars|page=[^&]+|keyword=[^&]+)&?)+')
def pagination():
    if plugin.path == '/search' and 'keyword' not in plugin.query:
        keyboard = Keyboard()
        keyboard.doModal()

        if keyboard.isConfirmed():
            response = request(plugin.pathqs + '&keyword=' + keyboard.getText())
        else:
            return
    else:
        response = request(plugin.pathqs)

    document = BeautifulSoup(response.text, 'html.parser').find('ul', {'class': ['list-episode-item', 'list-star']})
    items = []

    if document is not None:
        if plugin.path == '/list-star.html' or ('type' in plugin.query and 'stars' in plugin.query['type']):
            for li in document.find_all('li', recursive=False):
                plot = li.find('ul')
                item = ListItem(li.find('img').attrs['alt'])
                item.setArt({'poster': li.find('img').attrs['data-original']})
                item.setInfo('video', {'plot': '' if plot is None else plot.text})
                items.append((plugin.url_for(li.find('a').attrs['href']), item, True))

        elif plugin.path in ('/most-popular-drama', '/search'):
            InternalDatabase.connect()

            for a in document.find_all('a'):
                path = a.attrs['href']
                drama = drama_detail(path)
                item = ListItem(drama['title'])
                item.setArt({'poster': drama.pop('poster')})
                item.setInfo('video', drama)
                items.append((plugin.url_for(path), item, True))

            InternalDatabase.close()
        else:
            for a in document.find_all('a'):
                item = ListItem(u'[{}] {} {}'.format(a.find('span', {'class': 'type'}).text, a.find('h3').text, a.find('span', {'class': 'ep'}).text))
                item.setArt({'poster': a.find('img').attrs['data-original']})
                item.setInfo('video', {})
                item.setProperty('IsPlayable', 'true')
                items.append((plugin.url_for(a.attrs['href']), item, False))

        document = document.find_next_sibling()

        if document is not None:
            for li in document.find_all('li', {'class': ['next', 'previous']}):
                item = ListItem(localized_str(33600 if li.text == 'Next >' else 33601))
                items.append((plugin.url_for(plugin.path + li.find('a').attrs['href']), item, True))

    xbmcplugin.setContent(plugin.handle, 'videos')
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/star/[^/]+')
def star():
    response = request(plugin.path)
    document = BeautifulSoup(response.text, 'html.parser')
    InternalDatabase.connect()
    items = []

    for a in document.find('ul', {'class': 'list-episode-item'}).find_all('a'):
        path = a.attrs['href']
        drama = drama_detail(path)
        item = ListItem(drama['title'])
        item.setArt({'poster': drama.pop('poster')})
        item.setInfo('video', drama)
        items.append((plugin.url_for(path), item, True))

    InternalDatabase.close()
    xbmcplugin.setContent(plugin.handle, 'videos')
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/drama-list')
def drama_list():
    items = [(plugin.url_for('/filter-select/category/korean-drama'), ListItem(localized_str(33200)), True),
             (plugin.url_for('/filter-select/category/japanese-drama'), ListItem(localized_str(33201)), True),
             (plugin.url_for('/filter-select/category/taiwanese-drama'), ListItem(localized_str(33202)), True),
             (plugin.url_for('/filter-select/category/hong-kong-drama'), ListItem(localized_str(33203)), True),
             (plugin.url_for('/filter-select/category/chinese-drama'), ListItem(localized_str(33204)), True),
             (plugin.url_for('/filter-select/category/other-asia-drama'), ListItem(localized_str(33205)), True),
             (plugin.url_for('/filter-select/category/thailand-drama'), ListItem(localized_str(33206)), True)]

    xbmcplugin.setContent(plugin.handle, 'videos')
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/drama-movie')
def drama_movie():
    items = [(plugin.url_for('/filter-select/category/korean-movies'), ListItem(localized_str(33300)), True),
             (plugin.url_for('/filter-select/category/japanese-movies'), ListItem(localized_str(33301)), True),
             (plugin.url_for('/filter-select/category/taiwanese-movies'), ListItem(localized_str(33302)), True),
             (plugin.url_for('/filter-select/category/hong-kong-movies'), ListItem(localized_str(33303)), True),
             (plugin.url_for('/filter-select/category/chinese-movies'), ListItem(localized_str(33304)), True),
             (plugin.url_for('/filter-select/category/american-movies'), ListItem(localized_str(33305)), True),
             (plugin.url_for('/filter-select/category/other-asia-movies'), ListItem(localized_str(33306)), True),
             (plugin.url_for('/filter-select/category/thailand-movies'), ListItem(localized_str(33307)), True)]

    xbmcplugin.setContent(plugin.handle, 'videos')
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/filter-select/(?P<path>.+)')
def filter_select(path):
    items = [(plugin.url_for('/filter-select-id/char/' + path), ListItem(localized_str(33400)), True),
             (plugin.url_for('/filter-select-id/year/' + path), ListItem(localized_str(33401)), True),
             (plugin.url_for('/filter-select-id/status/' + path), ListItem(localized_str(33402)), True)]

    xbmcplugin.setContent(plugin.handle, 'videos')
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/filter-select-id/(?P<select_id>[^/]+)(?P<path>/.+)')
def filter_select_id(select_id, path):
    response = request(path)
    document = BeautifulSoup(response.text, 'html.parser')
    items = []

    if select_id == 'char':
        for div in document.find_all('div', {'class': 'list-content'}):
            select_value = div.find('h4').text
            item = ListItem(select_value)
            items.append((plugin.url_for('/list-select-id/{}/{}{}'.format(select_id, ord(select_value), path)), item, True))
    else:
        for option in document.find('select', {'id': 'select-{}'.format(select_id)}).find_all('option')[1:]:
            item = ListItem(option.text)
            items.append((plugin.url_for('/list-select-id/{}/{}{}'.format(select_id, option.attrs['value'], path)), item, True))

    xbmcplugin.setContent(plugin.handle, 'videos')
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/list-select-id/(?P<select_id>[^/]+)/(?P<select_value>[^/]+)(?P<path>/.+)')
def list_select_id(select_id, select_value, path):
    InternalDatabase.connect()
    response = request(path)
    document = BeautifulSoup(response.text, 'html.parser')
    items = []

    if select_id == 'char':
        select_value = chr(int(select_value))

        for div in document.find_all('div', {'class': 'list-content'}):
            if div.find('h4').text == select_value:
                for a in div.find('ul', {'class': 'filter-char'}).find_all('a'):
                    path = a.attrs['href']
                    drama = drama_detail(path)
                    item = ListItem(drama['title'])
                    item.setArt({'poster': drama.pop('poster')})
                    item.setInfo('video', drama)
                    items.append((plugin.url_for(path), item, True))

                break
    else:
        for li in document.find_all('li', {'class': '{}_{}'.format(select_id, select_value)}):
            path = li.find('a').attrs['href']
            drama = drama_detail(path)
            item = ListItem(drama['title'])
            item.setArt({'poster': drama.pop('poster')})
            item.setInfo('video', drama)
            items.append((plugin.url_for(path), item, True))

    InternalDatabase.close()
    xbmcplugin.setContent(plugin.handle, 'videos')
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/drama-detail/.+')
def list_episode():
    ExternalDatabase.connect()
    ExternalDatabase.add(plugin.path)
    ExternalDatabase.close()
    response = request(plugin.path)
    document = BeautifulSoup(response.text, 'html.parser').find('ul', {'class': 'all-episode'})
    items = []

    for a in reversed(document.find_all('a')):
        item = ListItem('[{}] {}'.format(a.find('span').text, a.find('h3').text.strip('\n ')))
        item.setInfo('video', {})
        item.setProperty('IsPlayable', 'true')
        items.append((plugin.url_for(a.attrs['href']), item, False))

    xbmcplugin.setContent(plugin.handle, 'videos')
    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/[^/]+.html')
def play_episode():
    response = request(plugin.path)
    document = BeautifulSoup(response.text, 'html.parser')
    title = document.find('h1').text.strip()
    all_server = document.find_all('li', {'data-video': True})
    position = Dialog().select(localized_str(33500), [server.contents[0] for server in all_server])

    if position != -1:
        xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
        resolveurl.add_plugin_dirs(__plugins__)

        try:
            url = resolveurl.resolve(all_server[position].attrs['data-video'])

            if url:
                item = ListItem(title, path=url)
                sub = re.search('&sub=([^&]+)', all_server[position].attrs['data-video'])

                if sub:
                    response = session.get('https://embed.watchasian.to/player/sub/index.php?id=' + sub.group(1))
                    item.setSubtitles([__temp__])

                    with open(__temp__, 'w') as o:
                        for i, text in enumerate(re.split('WEBVTT\r\n\r\n|\r\n\r\n', response.text)[1:], start=1):
                            o.write('{}\r\n{}\r\n\r\n'.format(i, text.encode('utf-8')))

                xbmcplugin.setResolvedUrl(plugin.handle, True, item)
            else:
                raise
        except:
            Dialog().notification(localized_str(33501), '')

        xbmc.executebuiltin('Dialog.Close(busydialognocancel)')


def drama_detail(path):
    drama = InternalDatabase.fetchone(path)

    if drama is None:
        response = request(path)
        document = BeautifulSoup(response.content, 'html.parser')
        element = document.find('div', {'class': 'details'})
        year = document.find('span', text='Released:').find_next_sibling('a').text
        InternalDatabase.add((path,
                              element.find('img').attrs['src'],
                              element.find('h1').text,
                              element.find('span', text=re.compile('Description:?')).parent.find_next_sibling().text,
                              document.find('span', text=re.compile('Country: ?')).next_sibling.strip(),
                              document.find('span', text='Status:').find_next_sibling('a').text,
                              int(year) if year.isdigit() else None))
        drama = InternalDatabase.fetchone(path)

    return drama


def request(path):
    for domain in domains:
        response = session.get(domain + path)

        if response.status_code == 200:
            return response


def create_database():
    InternalDatabase.connect()

    for path in ['/drama-list', '/kshow']:
        response = request(path)
        document = BeautifulSoup(response.content, 'html.parser')

        for li in document.find_all('li', {'class': 'filter-item'}):
            drama_detail(li.find('a').attrs['href'])

    InternalDatabase.close()


if __name__ == '__main__':
    plugin.run()
