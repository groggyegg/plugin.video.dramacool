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

try:
    from xbmc import executebuiltin, Keyboard, sleep
    from xbmcaddon import Addon
    from xbmcgui import Dialog, ListItem
    from xbmcplugin import addDirectoryItems, addSortMethod, endOfDirectory, setContent, setResolvedUrl, SORT_METHOD_TITLE, SORT_METHOD_VIDEO_YEAR
    from xbmcvfs import translatePath
except ImportError:
    SORT_METHOD_TITLE = None
    SORT_METHOD_VIDEO_YEAR = None


    class Addon(object):
        def getAddonInfo(self, id):
            return id

        def getLocalizedString(self, id):
            return id


    class Dialog(object):
        def notification(self, heading, message, icon=None, time=5000, sound=True):
            pass

        def select(self, heading, list, autoclose=None, preselect=None, useDetails=False):
            pass


    class Keyboard(object):
        def doModal(self, autoclose=None):
            pass

        def getText(self):
            pass

        def isConfirmed(self):
            pass


    class ListItem(object):
        def __init__(self, label='', label2='', path='', offscreen=False):
            pass

        def setArt(self, values):
            pass

        def setInfo(self, type, infoLabels):
            pass

        def setLabel(self, label):
            pass

        def setPath(self, path):
            pass

        def setProperty(self, key, value):
            pass

        def setSubtitles(self, subtitleFiles):
            pass


    def addDirectoryItems(handle, items, totalItems=None):
        pass


    def addSortMethod(handle, sortMethod, labelMask=None, label2Mask=None):
        pass


    def endOfDirectory(handle, succeeded=True, updateListing=False, cacheToDisc=True):
        pass


    def executebuiltin(function, wait=False):
        pass


    def setContent(handle, content):
        pass


    def sleep(time):
        pass


    def translatePath(path):
        return path


    def setResolvedUrl(handle, succeeded, listitem):
        pass

getAddonInfo = Addon().getAddonInfo
getLocalizedString = Addon().getLocalizedString
