"""UI module for DiscordZ."""
import curses
import time

import subwin
import ui_box
import wrapper


class UI:
    """UI class."""

    def __init__(self, window, theme, client):
        self.window = window
        self.theme = theme
        self.client = client
        theme.refresh_layout(window)
        self.maxyx = window.getmaxyx()
        self._queue = []

        self.server = None
        self.channel = None

        self.servers = {server.id: wrapper.Server(server) for server in client.servers}
        self.servers[0] = wrapper.DirectMessages(client)
        self.serv = ui_box.WinServ.from_rect(self)
        self.chan = ui_box.WinChan.from_rect(self)
        self.user = ui_box.WinUser.from_rect(self)
        self.status = ui_box.WinStatus.from_rect(self)
        self.box = ui_box.WinBox.from_rect(self)
        self.pad = ui_box.WinPad.from_rect(self)
        boxes = [self.serv, self.chan, self.user, self.status, self.box, self.pad]
        self.boxes = [box for box in boxes if box is not None]

        self.FOCUS_SHORTCUTS = {21: self.user, 19: self.serv, 3: self.chan, 8: self.pad, 0: self.box}

        self._focus = None
        self.focus(self.serv if theme.get_layout('serv') is not None else self.pad)
        self.theme.borders(self.window)

    def queue(self, func, *args, **kwargs):
        self._queue.append((func, args, kwargs))

    async def do(self):
        stop = time.time() + 0.2
        operations = 0
        for (func, args, kwargs) in self._queue:
            await func(*args, *kwargs)
            operations += 1
            if time.time() > stop:
                break
        self._queue = self._queue[operations:]

    async def update(self):
        for server in self.servers.values():
            await server.update(self.client)

    def set_server(self, server):
        if self.server is not None:
            self.server.focus_off()
        self.server = server
        if server is not None:
            server.focus_on()
            print('focusing on', server.name, file=open('2.log', 'a'))
            print(server.default_channel, file=open('2.log', 'a'))
            if server.focused_channel is None:
                self.set_channel(server.default_channel)
            else:
                self.set_channel(server.focused_channel)

    def set_channel(self, channel):
        print('setting', channel, file=open('2.log', 'a'))
        if self.channel is not None:
            self.channel.focus_off()
        self.channel = channel
        if channel is not None:
            channel.focus_on()
            self.queue(channel.load_logs, self.client)
        if self.server is not None:
            self.server.focused_channel = channel

    def refresh(self):
        for box in self.boxes:
            box.refresh()

    def focus(self, box: subwin.Win):
        if self._focus == box:
            return
        if self._focus is not None:
            self._focus.focus_off()
        self._focus = box
        box.focus_on()

    def press(self, key):
        """Handle key events."""
        if key in self.FOCUS_SHORTCUTS:
            self.focus(self.FOCUS_SHORTCUTS[key])
            return
        if self._focus is not None:
            self._focus.press(key)

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
            if box is not None:
                box.draw_()
