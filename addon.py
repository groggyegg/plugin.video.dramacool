from resources.lib import watchasian
from routing import Plugin
from xbmc import Keyboard
from xbmcaddon import Addon
from xbmcgui import ListItem

import os
import shutil
import xbmc
import xbmcplugin

try:
    import cPickle as pickle
except:
    import pickle

plugin = Plugin()
profile = xbmc.translatePath(Addon().getAddonInfo('profile'))
profile_cache = os.path.join(profile, 'cache')
profile_version = os.path.join(profile, 'version')
version = (1, 4, 3)


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
    watchasian.drama_pagination_list(plugin, '/search', '?type=movies&keyword=' + keyword + '&page=' + plugin.args['page'][0])


@plugin.route('/recently-added')
def recently_added():
    xbmcplugin.setPluginCategory(plugin.handle, 'Recently Added Drama')
    watchasian.episode_pagination_list(plugin, '/recently-added', '?page=' + plugin.args['page'][0])


@plugin.route('/recently-added-movie')
def recently_added_movie():
    xbmcplugin.setPluginCategory(plugin.handle, 'Recently Added Movie')
    watchasian.episode_pagination_list(plugin, '/recently-added-movie', '?page=' + plugin.args['page'][0])


@plugin.route('/recently-added-kshow')
def recently_added_kshow():
    xbmcplugin.setPluginCategory(plugin.handle, 'Recently Added Korean Show')
    watchasian.episode_pagination_list(plugin, '/recently-added-kshow', '?page=' + plugin.args['page'][0])


@plugin.route('/most-popular-drama')
def most_popular_drama():
    xbmcplugin.setPluginCategory(plugin.handle, 'Popular Drama')
    watchasian.drama_pagination_list(plugin, '/most-popular-drama', '?page=' + plugin.args['page'][0])


@plugin.route('/category/<category_id>')
def category(category_id):
    xbmcplugin.setPluginCategory(plugin.handle, category_id.replace('-', ' ').title())

    if 'block' in plugin.args:
        watchasian.drama_category_list(plugin, '/category/' + category_id, plugin.args['block'][0])
    else:
        watchasian.block_category_list(plugin, '/category/' + category_id)


@plugin.route('/kshow')
def kshow():
    xbmcplugin.setPluginCategory(plugin.handle, 'Korean Show')

    if 'block' in plugin.args:
        watchasian.drama_category_list(plugin, '/kshow', plugin.args['block'][0])
    else:
        watchasian.block_category_list(plugin, '/kshow')


@plugin.route('/drama-detail/<drama_id>')
def drama_detail(drama_id):
    watchasian.drama_episode_list(plugin, '/drama-detail/' + drama_id)


@plugin.route('/episode-detail/<episode_id>')
def episode_detail(episode_id):
    watchasian.resolve_episode(plugin, '/' + episode_id)


if __name__ == '__main__':
    plugin.run()
