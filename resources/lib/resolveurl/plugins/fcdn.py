"""
    Plugin for ResolveUrl
    Copyright (C) 2020 groggyegg

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import re
from resolveurl.plugins.lib import helpers
from resolveurl import common
from resolveurl.resolver import ResolveUrl


class FcdnResolver(ResolveUrl):
    name = "fcdn"
    domains = ['fcdn.stream']
    pattern = r'(?://|\.)(fcdn\.stream)/(?:v/)?([0-9a-zA-Z-]+)'

    def get_media_url(self, host, media_id):
        headers = {'User-Agent': common.RAND_UA}
        html = self.net.http_POST(self.get_url(host, media_id), {'d': host}, headers=headers).content
        sources = [(label, url.replace('\\/', '/')) for (url, label) in re.findall(r'"([^"]+)","label":"([^"]+)"', html)]
        return helpers.pick_source(sources) + helpers.append_headers(headers)

    def get_url(self, host, media_id):
        return self._default_get_url(host, media_id, template='https://{host}/api/source/{media_id}')

    @classmethod
    def _is_enabled(cls):
        return True
