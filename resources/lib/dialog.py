from xbmcgui import Dialog, WindowXMLDialog

import xbmcaddon
import xbmcvfs

ACTION_PREVIOUS_MENU = 10
ACTION_PLAYER_STOP = 13
ACTION_NAV_BACK = 92
PATH = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path'))


class Button:
    def __init__(self, window, controlid, heading, options):
        self.label = window.getControl(controlid)
        self.label.setLabel(f'{heading} [0/{len(options)}]')
        self.heading = heading
        self.options = options
        self.items = []

    def onclick(self, controlid):
        if self.label.getId() == controlid:
            selected = Dialog().multiselect(self.heading, self.options, preselect=self.items)

            if selected is not None:
                self.items = [self.options[i] for i in selected]
                self.label.setLabel(f'{self.heading} [{len(selected)}/{len(self.options)}]')

    def clear(self):
        self.items.clear()
        self.label.setLabel(f'{self.heading} [0/{len(self.options)}]')


class FilterDialog(WindowXMLDialog):
    OK = 9100
    CLEAR = 9200

    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, 'Filter.xml', PATH, defaultRes='1080i')

    def __init__(self, charlist, genrelist, statuslist, yearlist):
        self.charlist = charlist
        self.genrelist = genrelist
        self.statuslist = statuslist
        self.yearlist = yearlist
        self.buttons = None
        self.cancelled = False

    def onInit(self):
        self.buttons = [Button(self, 5500, 'Character', self.charlist),
                        Button(self, 5600, 'Year', self.yearlist),
                        Button(self, 5700, 'Genre', self.genrelist),
                        Button(self, 5800, 'Status', self.statuslist)]

    def onAction(self, action):
        if action.getId() in (ACTION_PREVIOUS_MENU, ACTION_NAV_BACK, ACTION_PLAYER_STOP):
            self.cancelled = True
            self.close()

    def onClick(self, controlId):
        for button in self.buttons:
            button.onclick(controlId)

        if controlId == FilterDialog.OK:
            self.close()

        if controlId == FilterDialog.CLEAR:
            for button in self.buttons:
                button.clear()

    def result(self):
        return dict(zip(['chars', 'years', 'genres', 'statuses'], [button.items for button in self.buttons]))
