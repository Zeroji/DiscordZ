"""UI module for DiscordZ."""
import curses
import discord
import subwin
import utils


class UI:
    """UI class."""

    def __init__(self, window, theme, client):
        self.window = window
        self.theme = theme
        self.client = client
        theme.refresh_layout(window)
        self.serv = WinServ.from_rect(self)
        self.chan = WinChan.from_rect(self)
        self.user = WinUser.from_rect(self)
        self.status = WinStatus.from_rect(self)
        self.box = WinBox.from_rect(self)
        self.pad = WinPad.from_rect(self)
        boxes = [self.serv, self.chan, self.user, self.status, self.box, self.pad]
        self.boxes = [box for box in boxes if box is not None]

        self.FOCUS_SHORTCUTS = {21: self.user, 19: self.serv, 3: self.chan, 8: self.pad, 0: self.box}

        self.focus = self.serv if theme.get_layout('serv') is not None else self.pad

        self.maxyx = window.getmaxyx()

        self.server = None
        self.channel = None

        self.servers = {}

        for channel in client.get_all_channels():
            if channel.server not in self.servers.keys():
                self.servers[(channel.server.name, channel.server)] = []
            self.servers[(channel.server.name, channel.server)].append(channel)

    def refresh(self):
        for box in self.boxes:
            box.refresh()

    def press(self, key):
        """Handle key events."""
        if key in self.FOCUS_SHORTCUTS:
            self.focus = self.FOCUS_SHORTCUTS[key]
            return
        if self.focus is not None:
            self.focus.press(key)

    def draw(self):
        """Draw the UI."""
        if self.maxyx != self.window.getmaxyx():
            self.maxyx = self.window.getmaxyx()
            curses.resize_term(*self.maxyx)
            self.theme.refresh_layout(self.window)
            for box in self.boxes:
                box.clear()
                box.update_rect(self.theme)
        self.theme.borders(self.window)

        for box in self.boxes:
            box.draw(box == self.focus)


class WinServ(subwin.WinList):
    win_name = 'serv'

    def __init__(self, window, ui):
        super().__init__(window, ui)
        self.data = [0]
        self.data_to_text = lambda s: 'Friends' if s == 0 else s.name
        self.data_to_key = self.data_to_text
        servers = list(ui.client.servers)
        servers.sort(key=self.data_to_key)
        self.data.extend(servers)
        self.pair_main = self.ui.theme.pair('main')

    def press(self, key):
        super(WinServ, self).press(key)
        if key == 10:
            self.ui.server = self.data[self.cursor]
            self.ui.channel = None
            self.ui.focus = self.ui.chan
            self.ui.chan.update()


class WinChan(subwin.WinList):
    win_name = 'chan'

    def __init__(self, window, ui):
        super().__init__(window, ui)
        self.data_to_key = lambda s: s.name or s.recipients[0].name
        self.data_to_text = utils.channel_name

    def update(self):  # Refresh data
        self.win.clear()
        if self.ui.server == 0:
            self.data = list(self.ui.client.private_channels)
        else:
            channels = [channel for channel in self.ui.server.channels if channel.type == discord.ChannelType.text]
            channels.sort(key=lambda chan: chan.position)
            self.data = channels

    def press(self, key):
        super().press(key)
        if key == 10:
            self.ui.channel = self.data[self.cursor]


class WinUser(subwin.Win):
    win_name = 'user'


class WinStatus(subwin.Win):
    win_name = 'status'

    def draw(self, _):
        """Draw status bar."""
        message = ''
        channel = self.ui.channel
        if self.ui.server is None:
            message = 'DiscordZ - connected as ' + self.ui.client.user.name
        else:
            if self.ui.server != 0:
                message = self.ui.server.name
            if channel is not None:
                if channel.name is None:
                    message += '@'
                message += utils.channel_name(channel)
                if channel.topic is not None and len(channel.topic.strip()) > 0:
                    message += ' - '
                    max_length = self.width - len(message)
                    message += utils.slide_text(self.ui.channel.topic, max_length, max_length // 3, 0.1)
        self.clear()
        self.addstr(0, 0, message, self.ui.theme.pair('main'))


class WinBox(subwin.Win):
    win_name = 'box'


class WinPad(subwin.Win):
    win_name = 'pad'
