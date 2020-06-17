from bs4 import BeautifulSoup
from routing import Plugin
from StorageServer import StorageServer
from xbmc import Keyboard
from xbmcaddon import Addon
from xbmcgui import Dialog, DialogProgress, ListItem, Window

import _strptime
import os
import pickle
import re
import resolveurl
import requests
import shutil
import time
import xbmc
import xbmcplugin

cache = StorageServer('plugin.video.dramacool', 24)
domain = 'https://www4.watchasian.to'
plugin = Plugin()
profile = xbmc.translatePath(Addon().getAddonInfo('profile'))
profile_cache = os.path.join(profile, 'cache')
profile_version = os.path.join(profile, 'version')
version = (1, 4, 0)


@plugin.route('/')
def index():
    if not os.path.exists(profile_version):
        os.makedirs(profile_cache)

        with open(profile_version, 'wb') as o:
            pickle.dump(version, o, pickle.HIGHEST_PROTOCOL)
    else:
        with open(profile_version, 'rb+') as io:
            if version > pickle.load(io):
                io.seek(0)
                pickle.dump(version, io, pickle.HIGHEST_PROTOCOL)
                shutil.rmtree(profile_cache)
                os.makedirs(profile_cache)

    xbmcplugin.setPluginCategory(plugin.handle, 'Categories')
    xbmcplugin.setContent(plugin.handle, 'videos')
    items = [(plugin.url_for_path('/search?type=movies&page=1'), ListItem('Search'), True),
             (plugin.url_for_path('/recently-added?page=1'), ListItem('Recently Added Drama'), True),
             (plugin.url_for_path('/recently-added-movie?page=1'), ListItem('Recently Added Movie'), True),
             (plugin.url_for_path('/recently-added-kshow?page=1'), ListItem('Recently Added Korean Show'), True),
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
    xbmcplugin.setContent(plugin.handle, 'videos')
    headers = {'referer': domain}
    response = requests.get(domain + '/search?type=movies&keyword=' + keyword + '&page=' + plugin.args['page'][0], headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser').find('ul', {'class': 'switch-block list-episode-item'})
        items = []

        for episode in soup.find_all('li'):
            path = episode.find('a').attrs['href']
            info = cache.cacheFunction(drama_detail_info, path)
            item = ListItem(info['video']['title'])
            item.setArt({'poster': info['poster']})
            item.setInfo('video', info['video'])
            items.append((plugin.url_for_path(path), item, True))

        for page in soup.find_next_sibling().find_all_next('li', {'class': ['next', 'previous']}):
            title = '[B]' + page.text + '[/B]'
            path = '/search' + page.find('a').attrs['href']
            item = ListItem(title)
            items.append((plugin.url_for_path(path), item, True))

        xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/recently-added')
def recently_added():
    xbmcplugin.setPluginCategory(plugin.handle, 'Recently Added Drama')
    recently('/recently-added?page=' + plugin.args['page'][0])


@plugin.route('/recently-added-movie')
def recently_added_movie():
    xbmcplugin.setPluginCategory(plugin.handle, 'Recently Added Movie')
    recently('/recently-added-movie?page=' + plugin.args['page'][0])


@plugin.route('/recently-added-kshow')
def recently_added_kshow():
    xbmcplugin.setPluginCategory(plugin.handle, 'Recently Added Korean Show')
    recently('/recently-added-kshow?page=' + plugin.args['page'][0])


@plugin.route('/category/<category_id>')
def category(category_id):
    xbmcplugin.setPluginCategory(plugin.handle, category_id.replace('-', ' ').title())

    if 'block' in plugin.args:
        category_drama('/category/' + category_id, plugin.args['block'][0])
    else:
        category_block('/category/' + category_id)


@plugin.route('/kshow')
def kshow():
    xbmcplugin.setPluginCategory(plugin.handle, 'Korean Show')

    if 'block' in plugin.args:
        category_drama('/kshow', plugin.args['block'][0])
    else:
        category_block('/kshow')


@plugin.route('/drama-detail/<drama_id>')
def drama_detail(drama_id):
    info = cache.cacheFunction(drama_detail_info, '/drama-detail/' + drama_id)
    xbmcplugin.setPluginCategory(plugin.handle, info['video']['title'])
    xbmcplugin.setContent(plugin.handle, 'videos')
    response = requests.get(domain + '/drama-detail/' + drama_id)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser').find('ul', {'class': 'list-episode-item-2 all-episode'})
        items = []

        for episode in soup.find_all('li'):
            title = '[' + episode.find('span').text + '] ' + episode.find('h3').text.replace('\n', '').strip()
            info['video']['title'] = title
            path = '/episode-detail' + episode.find('a').attrs['href']
            item = ListItem(title)
            item.setArt({'poster': info['poster']})
            item.setInfo('video', info['video'])
            item.setProperty('IsPlayable', 'true')
            items.append((plugin.url_for_path(path), item, False))

        xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/episode-detail/<episode_id>')
def episode_detail(episode_id):
    window = Window(10101)
    progress = DialogProgress()
    progress.create('Loading Video')
    xbmc.sleep(100)
    button = window.getControl(10)
    button.setEnabled(False)
    response = requests.get(domain + '/' + episode_id)
    progress.update(25)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser').find('div', {'class': 'block watch-drama'})
        items = []
        progress.update(50)

        for server in soup.find('div', {'class': 'anime_muti_link'}).find_all('li'):
            item = ListItem(server.next.title(), re.sub('^//', 'https://', server.attrs['data-video']))
            items.append(item)

        position = Dialog().select('Choose Server', items)
        progress.update(75)

        if position != -1:
            url = resolveurl.resolve(items[position].getLabel2())
            progress.update(100)

            if url:
                item = ListItem(soup.find('h1').text.strip())
                xbmc.Player().play(url, item)
            else:
                Dialog().notification('Couldn\'t Resolve Server', '')

    progress.close()
    button.setEnabled(True)


def drama_detail_info(path):
    url = domain + path
    path = os.path.join(profile_cache, path.rsplit('/', 1)[1])

    if os.path.exists(path):
        with open(path, 'rb') as i:
            return pickle.load(i)
    else:
        response = requests.get(url)

        if response.status_code == 200:
            details = BeautifulSoup(response.text, 'html.parser').find('div', {'class': 'info'})
            poster = details.find_previous().attrs['src']
            title = details.find('h1').text.strip()
            director = details.find('span', text='Director:')
            country = details.find('span', text='Country: ')
            status = details.find('span', text='Status:')
            year = details.find('span', text='Released:')
            genre = details.find('span', text='Genre:')
            aired = details.find('span', text='Airs:')
            info = {'title': title,
                    'plot': details.find('span', text='Description').find_next().text,
                    'director': '' if director is None else director.next_sibling.title(),
                    'country': '' if country is None else country.next_sibling.title(),
                    'status': '' if status is None else status.find_next().text,
                    'year': '' if year is None else year.find_next().text,
                    'genre': '' if genre is None else [a.text for a in genre.find_next_siblings()],
                    'aired': '' if aired is None else time.strftime('%Y-%m-%d', _strptime._strptime_time(aired.next_sibling.title(), ' %b %d, %Y')),
                    'mediatype': 'video'}

            if info['status'] == 'Completed':
                with open(path, 'wb') as o:
                    pickle.dump({'poster': poster, 'video': info}, o, pickle.HIGHEST_PROTOCOL)

            return {'poster': poster, 'video': info}


def recently(path):
    xbmcplugin.setContent(plugin.handle, 'videos')
    response = requests.get(domain + path)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser').find('ul', {'class': 'switch-block list-episode-item'})
        items = []

        for episode in soup.find_all('li'):
            title = '[' + episode.find('span').text + '] ' + episode.find('a').attrs['title']
            poster = episode.find('img').attrs['data-original']
            path = '/episode-detail' + episode.find('a').attrs['href']
            item = ListItem(title)
            item.setArt({'poster': poster})
            items.append((plugin.url_for_path(path), item, False))

        for page in soup.findAllNext('li', {'class': ['next', 'previous']}):
            title = '[B]' + page.text + '[/B]'
            path = '/recently-added' + page.find('a').attrs['href']
            item = ListItem(title)
            items.append((plugin.url_for_path(path), item, True))

        xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


def category_drama(path, block_id):
    xbmcplugin.setContent(plugin.handle, 'videos')
    response = requests.get(domain + path)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser').find('div', {'class': 'filter'}).find_next_sibling()

        for block in soup.find_all_next('div', {'class': 'list-content'}):
            if block.find_next('h4').text == block_id:
                items = []

                for content in block.find_all('li'):
                    path = content.find('a').attrs['href']
                    info = cache.cacheFunction(drama_detail_info, path)
                    item = ListItem(info['video']['title'])
                    item.setArt({'poster': info['poster']})
                    item.setInfo('video', info['video'])
                    items.append((plugin.url_for_path(path), item, True))

                xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
                break

    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.endOfDirectory(plugin.handle)


def category_block(path):
    xbmcplugin.setContent(plugin.handle, 'videos')
    response = requests.get(domain + path)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser').find('div', {'class': 'filter'}).find_next_sibling()
        items = []

        for block in soup.find_all_next('div', {'class': 'list-content'}):
            title = block.find_next('h4').text
            item = ListItem(title)
            items.append((plugin.url_for_path(path + '?block=' + title), item, True))

        xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


if __name__ == '__main__':
    plugin.run()
