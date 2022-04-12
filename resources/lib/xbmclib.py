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
