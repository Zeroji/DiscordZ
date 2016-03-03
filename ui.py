"""UI module for DiscordZ."""


class UI:
    """UI class."""

    def __init__(self, window, theme, client):
        self.window = window
        self.theme = theme
        self.client = client
        theme.refresh_layout(window)
        self.maxyx = window.getmaxyx()

        self.server = None
        self.channel = None

        self.servers = {}

        for channel in client.get_all_channels():
            if channel.server not in self.servers.keys():
                self.servers[(channel.server.name, channel.server)] = []
            self.servers[(channel.server.name, channel.server)].append(channel)

    def press(self, key, focus):
        """Handle keypresses."""
        val = None
        if focus in dir(self.theme):
            box = self.theme.__getattribute__(focus)
            if box is not None:
                val = self.__getattribute__('_key_' + focus)(box, key) or val
        return val

    def draw(self, focus):
        """Draw the UI."""
        if self.maxyx != self.window.getmaxyx():
            self.maxyx = self.window.getmaxyx()
            self.theme.refresh_layout(self.window)
        self.theme.borders(self.window)

        for box_name in self.theme.layout.order:
            box = self.theme.__getattribute__(box_name)
            if box is not None:
                box.clear()
                self.__getattribute__('draw_' + box_name)(
                    box, box_name == focus)

    def draw_status(self, win, focused):
        """Draw status bar."""
        # pylint: disable=E1101
        message = 'DiscordZ - connected as ' + self.client.user.name
        if self.server is not None:
            if self.server == 0:
                if self.channel is not None:
                    message += ' @' + self.channel.user.name
            else:
                message += ' on ' + self.server.name
                if self.channel is not None:
                    message += '#' + self.channel.name
        win.addstr(0, 0, message, self.theme.pair('main'))

    def _key_serv(self, win, key):
        server_keys = list(self.servers.keys())
        server_keys.sort()
        if key == 258 and win.cursor < len(self.servers):
            win.cursor += 1
        if key == 259 and win.cursor > 0:
            win.cursor -= 1
        if key == 10:
            if win.cursor == 0:
                self.server = 0
            else:
                self.server = server_keys[win.cursor - 1][1]
            return 'chan'

    def draw_serv(self, win, focused):
        """Draw server panel. Or bar. Whatever."""
        server_keys = list(self.servers.keys())
        server_keys.sort()
        for i in range(min(win.height, len(self.servers) + 1)):
            index = i + win.offset
            color = ((self.theme.pair('sel_focus') if focused else
                      self.theme.pair('sel')) if index == win.cursor else
                     self.theme.pair('main'))
            if index == 0:
                win.addlnstr(i, 0, ' PM', win.width, color)
            else:
                win.addlnstr(i, 0, server_keys[index - 1][0], win.width, color)

    def draw_chan(self, win, focused):
        """Draw channel panel. Or bar. Whatever."""
        color = self.theme.pair('main')
        win.addstr(0, 0, 'Hello.' + str(focused), color)

    def draw_user(self, win, focused):
        """Draw user panel. Or bar. Whatever."""
        color = self.theme.pair('main')
        win.addstr(0, 0, 'Hello.' + str(focused), color)

    def draw_pad(self, win, focused):
        """Draw main chat box."""
        color = self.theme.pair('main')
        win.addstr(0, 0, 'Main chat box!' + str(focused), color)

    def draw_box(self, win, focused):
        """Draw input box."""
        color = self.theme.pair('main')
        win.addstr(0, 0, 'Hi.' + str(focused), color)
