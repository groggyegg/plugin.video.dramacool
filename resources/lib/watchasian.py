from bs4 import BeautifulSoup
from xbmcaddon import Addon
from xbmcgui import Dialog, ListItem

import _strptime
import datetime
import os
import re
import requests
import resolveurl
import time
import xbmc
import xbmcplugin

try:
    import cPickle as pickle
except:
    import pickle

domain = 'https://www4.watchasian.to'
profile_cache = xbmc.translatePath(Addon().getAddonInfo('profile')) + 'cache'


def drama_detail_content(path):
    file_path = os.path.join(profile_cache, path.rsplit('/', 1)[1])

    if os.path.exists(file_path):
        with open(file_path, 'rb') as i:
            detail = pickle.load(i)

            if detail['video']['status'] == 'Completed':
                return detail
            elif (datetime.datetime.now() - datetime.datetime(*_strptime._strptime_time(detail['video']['dateadded'], '%Y-%m-%d %H:%M:%S')[:6])).days < 7:
                return detail

    response = requests.get(domain + path)

    if response.status_code == 200:
        detail = BeautifulSoup(response.text, 'html.parser').find('div', {'class': 'info'})
        poster = detail.find_previous().attrs['src']
        director = detail.find('span', text='Director:')
        year = detail.find('span', text='Released:')
        aired = detail.find('span', text='Airs:')
        video = {
            'title': detail.find('h1').text.strip(),
            'plot': detail.find('span', text='Description').find_next().text,
            'director': '' if director is None else director.next_sibling.title(),
            'country': detail.find('span', text='Country: ').next_sibling.title(),
            'status': detail.find('span', text='Status:').find_next().text,
            'year': '' if year is None else year.find_next().text,
            'genre': [a.text for a in detail.find('span', text='Genre:').find_next_siblings()],
            'aired': '' if aired is None else time.strftime('%Y-%m-%d', _strptime._strptime_time(aired.next_sibling.title(), ' %b %d, %Y')),
            'dateadded': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        with open(file_path, 'wb') as o:
            pickle.dump({'poster': poster, 'video': video}, o, pickle.HIGHEST_PROTOCOL)

        return {'poster': poster, 'video': video}


def block_category_list(plugin, path):
    xbmcplugin.setContent(plugin.handle, 'videos')
    response = requests.get(domain + path)
    items = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser').find('div', {'class': 'filter'}).find_next_sibling()

        for block in soup.find_all('div', {'class': 'list-content'}):
            block_title = block.find_next('h4').text

            item = ListItem(block_title)
            items.append((plugin.url_for_path(path + '?block=' + block_title), item, True))

    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


def drama_category_list(plugin, path, block_title):
    xbmcplugin.setContent(plugin.handle, 'videos')
    response = requests.get(domain + path)
    items = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser').find('div', {'class': 'filter'}).find_next_sibling()

        for block in soup.find_all('div', {'class': 'list-content'}):
            if block.find_next('h4').text == block_title:
                for drama in block.find_all('li'):
                    drama_path = drama.find('a').attrs['href']
                    drama_detail = drama_detail_content(drama_path)

                    item = ListItem(drama_detail['video']['title'])
                    item.setArt({'poster': drama_detail['poster']})
                    item.setInfo('video', drama_detail['video'])
                    items.append((plugin.url_for_path(drama_path), item, True))

                break

    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


def drama_episode_list(plugin, path):
    drama_detail = drama_detail_content(path)
    xbmcplugin.setPluginCategory(plugin.handle, drama_detail['video']['title'])
    xbmcplugin.setContent(plugin.handle, 'videos')
    response = requests.get(domain + path)
    items = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser').find('ul', {'class': 'list-episode-item-2 all-episode'})

        for episode in soup.find_all('li'):
            episode_title = '[' + episode.find('span').text + '] ' + episode.find('h3').text.replace('\n', '').strip()
            episode_path = '/episode-detail' + episode.find('a').attrs['href']
            drama_detail['video']['title'] = episode_title

            item = ListItem(episode_title)
            item.setArt({'poster': drama_detail['poster']})
            item.setInfo('video', drama_detail['video'])
            item.setProperty('IsPlayable', 'true')
            items.append((plugin.url_for_path(episode_path), item, False))

    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


def drama_pagination_list(plugin, path, query):
    xbmcplugin.setContent(plugin.handle, 'videos')
    response = requests.get(domain + path + query, headers={'referer': domain})
    items = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser').find('ul', {'class': 'switch-block list-episode-item'})

        if soup is not None:
            for drama in soup.find_all('li'):
                drama_path = drama.find('a').attrs['href']
                drama_detail = drama_detail_content(drama_path)

                item = ListItem(drama_detail['video']['title'])
                item.setArt({'poster': drama_detail['poster']})
                item.setInfo('video', drama_detail['video'])
                items.append((plugin.url_for_path(drama_path), item, True))

            soup = soup.find_next_sibling()

            if soup is not None:
                for page in soup.find_all('li', {'class': ['next', 'previous']}):
                    page_title = '[B]' + page.text + '[/B]'
                    page_path = path + page.find('a').attrs['href']

                    item = ListItem(page_title)
                    items.append((plugin.url_for_path(page_path), item, True))

    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


def episode_pagination_list(plugin, path, query):
    xbmcplugin.setContent(plugin.handle, 'videos')
    response = requests.get(domain + path + query)
    items = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser').find('ul', {'class': 'switch-block list-episode-item'})

        if soup is not None:
            for episode in soup.find_all('li'):
                episode_title = '[' + episode.find('span').text + '] ' + episode.find('a').attrs['title']
                episode_poster = episode.find('img').attrs['data-original']
                episode_path = '/episode-detail' + episode.find('a').attrs['href']

                item = ListItem(episode_title)
                item.setArt({'poster': episode_poster})
                item.setInfo('video', {})
                item.setProperty('IsPlayable', 'true')
                items.append((plugin.url_for_path(episode_path), item, False))

            soup = soup.find_next_sibling()

            if soup is not None:
                for page in soup.find_all('li', {'class': ['next', 'previous']}):
                    page_title = '[B]' + page.text + '[/B]'
                    page_path = path + page.find('a').attrs['href']

                    item = ListItem(page_title)
                    items.append((plugin.url_for_path(page_path), item, True))

    xbmcplugin.addDirectoryItems(plugin.handle, items, len(items))
    xbmcplugin.endOfDirectory(plugin.handle)


def resolve_episode(plugin, path):
    response = requests.get(domain + path)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser').find('div', {'class': 'block watch-drama'}).find('h1')
        items = []

        for link in soup.find_next_sibling('div', {'class': 'anime_muti_link'}).find_all('li'):
            item = ListItem(link.next.title(), path=re.sub('^//', 'https://', link.attrs['data-video']))
            items.append(item)

        position = Dialog().select('Choose Server', items)

        if position != -1:
            xbmc.executebuiltin("ActivateWindow(busydialog)")
            resolveurl.add_plugin_dirs(os.path.join(Addon().getAddonInfo('path'), 'resources/lib/resolveurl/plugins'))
            url = resolveurl.resolve(items[position].getPath())

            if url:
                item = ListItem(soup.text.strip(), path=url)
                xbmcplugin.setResolvedUrl(plugin.handle, True, item)
            else:
                Dialog().notification('Couldn\'t Resolve Server', '')
