
import wx, time
from tools import Events


class Icon(wx.TaskBarIcon):
    """notifier's taskbar icon"""

    def __init__(self, logo=None):
        wx.TaskBarIcon.__init__(self)
        if logo is not None:
            self.SetIcon(wx.Icon(logo, eval("wx.BITMAP_TYPE_%s" %
                logo.split(".")[-1].upper())))
        self.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self._open)
        self.Bind(wx.EVT_TASKBAR_RIGHT_DOWN, self._open)
        self.Bind(wx.EVT_MENU, self._select)
        Events.subscribe("menu.data", self._menu)

    def _open(self, event):
        Events.publish("menu.open", event)

    def _select(self, event):
        Events.publish("menu.select", 
            self._data[event.GetId()])

    def _menu(self, data):
        
        def generate(data):
            menu = wx.Menu()
            for item in data:
                if type(item) == str:
                    if "-" in item and len(item.replace("-", "")) == 0:
                        menu.AppendSeparator()
                    else:
                        id = len(self._data)
                        self._data[id] = item
                        menu.Append(id, item)
                elif hasattr(item, "__iter__"):
                    menu.AppendMenu(-1, item[0], generate(item[1:]))
            return menu

        self._data = {}
        self.PopupMenu(generate(data))
        
    def close(self):
        self.Destroy()


class Popup(wx.Frame):
    """notifier's popup window"""

    def __init__(self):

        wx.Frame.__init__(self, None, -1, 
            style=wx.NO_BORDER|wx.FRAME_NO_TASKBAR)
        self._padding = 12 # padding between edge, icon and text
        self.visible = False

        # platform specific hacks
        lines = 2
        lineHeight = wx.MemoryDC().GetTextExtent(" ")[1]
        if wx.Platform == "__WXGTK__":
            # use the popup window widget on gtk as the
            # frame widget can't animate outside the screen
            self.popup = wx.PopupWindow(self, -1)
        elif wx.Platform == "__WXMSW__":
            # decrement line height on windows as the 
            # text calc below is off otherwise
            self.popup = self
            lineHeight -= 3
        elif wx.Platform == "__WXMAC__":
            # untested
            self.popup = self

        self.popup.SetSize((250, 
            (lineHeight * (lines + 1)) + (self._padding * 2)))
        self.panel = wx.Panel(self.popup, -1, size=self.popup.GetSize())

        # popup's click handler
        self.panel.Bind(wx.EVT_LEFT_DOWN, self._click)

    def _click(self, event):
        self.hide()
        Events.publish("popup.click", self.text.GetLabel())

    def show(self, text, logo=None):
        """shows the popup"""

        logoWidth = 0
        horizPads = 2
        popupSize = self.popup.GetSize()
        
        # add logo
        if hasattr(self, "logo"):
            self.logo.Destroy()
        if logo is not None:
            self.logo = logo = wx.Bitmap(logo)
            logoWidth = self.logo.GetSize().width
            wx.StaticBitmap(self.panel, -1, 
                pos=(self._padding, self._padding)).SetBitmap(self.logo)
            horizPads = 3

        # add text
        if hasattr(self, "text"):
            self.text.Destroy()
        self.text = wx.StaticText(self.panel, -1, text)
        self.text.Move((logoWidth + (self._padding * 2), self._padding))
        self.text.SetSize((popupSize.width - logoWidth - 
            (self._padding * horizPads), popupSize.height - 
            (self._padding * 2)))
        self.text.Bind(wx.EVT_LEFT_DOWN, self._click)

        # animate
        screen = wx.GetClientDisplayRect()
        self.visible = True
        self.popup.Show()
        for i in range(1, popupSize.height + 1):
            self.popup.Move((screen.width - popupSize.width, 
                screen.height - i))
            self.popup.SetTransparent(int(240. / popupSize.height * i))
            self.popup.Update()
            self.popup.Refresh()
            time.sleep(.01)

    def hide(self):
        """hides the popup"""
        self.popup.Hide()
        self.visible = False

    def focused(self):
        """returns true if popup has mouse focus"""
        mouse = wx.GetMousePosition()
        popup = self.popup.GetScreenRect()
        return (self.visible and mouse.x in 
            range(popup.x, popup.x + popup.width)
            and mouse.y in range(popup.y, popup.y + popup.height))


class Settings(wx.Frame):
    """notifier's settings window"""
    
    def __init__(self, settings, icon=None):
        
        self._settings = {}
        
        # set up window
        wx.Frame.__init__(self, None, -1, "Settings", 
            (-1, -1), (300, 100 + (35 * len(settings))), wx.CAPTION)
        panel = wx.Panel(self, -1, style=wx.RAISED_BORDER)
        grid = wx.GridBagSizer(10, 30)

        # create text entry for each setting
        for i, (name, value) in enumerate(settings.items()):
            i += 1
            style = wx.TE_LEFT
            if name.lower().startswith("pass"):
                style = style|wx.TE_PASSWORD
            self._settings[name] = wx.TextCtrl(panel, -1, value, style=style)
            grid.Add(wx.StaticText(panel, -1, name), (i, 1))
            grid.Add(self._settings[name], (i, 2))
        
        # add cancel/save buttons
        button = wx.Button(panel, -1, "Cancel")
        grid.Add(button, (len(settings) + 1, 1))
        button.Bind(wx.EVT_BUTTON, self.close)
        button = wx.Button(panel, -1, "Save")
        grid.Add(button, (len(settings) + 1, 2))
        button.Bind(wx.EVT_BUTTON, self.save)

        # show the window
        panel.SetSizer(grid)
        if icon:
            self.SetIcon(wx.Icon(icon, wx.BITMAP_TYPE_ICO))
        self.Centre()
        self.Show()
        
    def save(self, event):
        Events.publish("settings.save", dict([(setting, control.GetValue()) 
            for setting, control in self._settings.items()]))
        self.close(event)
        
    def close(self, event):
        Events.publish("settings.close")
        self.Destroy()


class Notifier(wx.App):
    """main notifier app"""

    def __init__(self, logo):
        wx.App.__init__(self, redirect=0)
        self.icon = Icon(logo)
        self.popup = Popup()
        self.settings = {}
        self._settingsOpen = False
        self._logo = logo
        self._items = []
        self._popped = 0
        self._delay = 4
        Events.subscribe("menu.open", self._menu)
        Events.subscribe("menu.select", self._select)
        Events.subscribe("popup.click", self.click)
        Events.subscribe("settings.save", self.save)
        Events.subscribe("settings.close", self._close)

    def _main(self, event):
        self.main()
        if self.popup.focused():
            # maintain opened state if focused
            self._popped = time.time()
        elif self.popup.visible:
            # hide the popup once delay is reached
            if self._popped + self._delay < time.time():
                self.popup.hide()
        elif self._items and not self._settingsOpen:
            self._popped = time.time()
            text, logo = self._items.pop(0)
            self.popup.show(text, logo)
        
    def _menu(self, event):
        menu = self.menu()
        separated = lambda check, name: (["-"] if check else []) + [name]
        if self.settings:
            menu += separated(menu, "Settings")
        menu += separated(menu, "Exit")
        Events.publish("menu.data", menu)

    def _select(self, item):
        if item == "Settings":
            self.showSettings()
        elif item == "Exit":
            self.exit()
            exit(0)
        else:
            self.select(item)

    def start(self):
        timer = wx.Timer(self, -1)
        self.Bind(wx.EVT_TIMER, self._main, timer)
        timer.Start(500)
        self.MainLoop()

    def showPopup(self, text, logo=None):
        self._items.append((text, logo))
        
    def showSettings(self):
        if not self._settingsOpen:
            if self._popped:
                self.popup.hide()
            self._settingsOpen = True
            Settings(self.settings, icon=self._logo)
    
    def _close(self, data=None):
        self._settingsOpen = False
        
    def exit(self):
        self.icon.close()
        self.Exit()

    def main(self):
        raise NotImplementedError

    def menu(self):
        raise NotImplementedError

    def select(self, item):
        raise NotImplementedError

    def click(self, item):
        raise NotImplementedError

    def save(self, settings):
        raise NotImplementedError


if __name__ == "__main__":
    
    class Test(Notifier):
        
        def __init__(self):
            import os.path
            Notifier.__init__(self, 
                os.path.join(os.path.dirname(__file__), "sl.ico"))
            self.settings = {"Username": "", "Password": ""}
        
        def main(self):
            self.showPopup("test %s" % time.time())
            
        def menu(self):
            return ["menu1",
                    "menu2",
                    "menu3",
                    ["menu4", 
                        "menu4a", 
                        ["menu4b", 
                            "menu4b1",
                            "menu4b2",
                            "menu4b3",],
                        "menu4c",],
                    "menu5",]
            
        def click(self, item):
            print "popup clicked: %s" % item
            
        def select(self, item):
            print "menu selected: %s" % item

        def save(self, settings):
            print "settings saved: %s" % settings
            
    test = Test()
    test.start()
