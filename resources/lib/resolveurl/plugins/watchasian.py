"""
    Plugin for ResolveURL
    Copyright (C) 2020 groggyegg

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import re
from resolveurl.plugins.lib import helpers
from resolveurl import common
from resolveurl.resolver import ResolveUrl, ResolverError


class WatchAsianResolver(ResolveUrl):
    name = "watchasian"
    domains = ['embed.watchasian.to', 'embed.dramacool.movie']
    pattern = r'(?://|\.)(embed\.(?:watchasian\.to|dramacool\.movie))/(?:[a-zA-Z]+).php\?(.+)'

    def get_media_url(self, host, media_id):
        web_url = self.get_url(host, media_id)
        headers = {'User-Agent': common.FF_USER_AGENT, 'X-Requested-With': 'XMLHttpRequest'}
        html = self.net.http_GET(web_url, headers=headers).content
        source = re.search('"file":"([^"]+)"', html)
        if source:
            headers.update({'verifypeer': 'false', 'Referer': host})
            return source.group(1).replace('\\/', '/') + helpers.append_headers(headers)
        raise ResolverError('Video cannot be located.')

    def get_url(self, host, media_id):
        return self._default_get_url(host, media_id, template='https://{host}/ajax.php?{media_id}')

    @classmethod
    def _is_enabled(cls):
        return True
