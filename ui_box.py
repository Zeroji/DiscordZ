import curses
import curses.textpad
import discord
import subwin
import utils
import wrapper


def display_item(self, item, row, sel):
    """Display a channel/server name, including mentions & unread status."""
    attr = self.pair_selection if sel else self.pair_main
    if item.unread and not item.focused:
        attr += curses.A_BOLD
    self.addlnstr(row, 0, self.data_to_text(item)[:self.width], self.width, attr)
    if item.mentions and not item.focused:
        attr = self.ui.theme.pair('mention_icon') + curses.A_BOLD
        text = str(item.mentions)
        self.addstr(row, self.width - len(text), text, attr)


class WinServ(subwin.WinList):
    """Server list box."""
    win_name = 'serv'

    def __init__(self, window, ui):
        super().__init__(window, ui)
        self.data_to_text = lambda s: s.name
        self.data_to_key = lambda s: s.name
        self.display = lambda i, r, s: display_item(self, i, r, s)
        servers = list(ui.servers.values())
        servers.sort(key=lambda s: '' if isinstance(s, wrapper.DirectMessages) else s.name)
        self.data = servers
        self.pair_main = self.ui.theme.pair('main')

    def press(self, key):
        super(WinServ, self).press(key)
        if key == 10:
            self.ui.set_server(self.data[self.cursor])
            self.ui.focus(self.ui.chan)
            self.ui.chan.update()
            self.ui.pad.redraw()
            self.ui.status.redraw()


class WinChan(subwin.WinList):
    """Channel list box."""
    win_name = 'chan'

    def __init__(self, window, ui):
        super().__init__(window, ui)
        self.data_to_key = lambda s: s.name
        self.data_to_text = lambda s: s.display_name
        self.display = lambda i, r, s: display_item(self, i, r, s)

    def update(self):  # Refresh data
        self.win.clear()
        server = self.ui.server
        self.data = server.channels
        if server.focused_channel is not None:
            print(server.focused_channel.name, file=open('2.log', 'a'))
            self.cursor = server.channels.index(server.focused_channel)
            if self.cursor >= self.height:
                self.offset = self.cursor - self.height + 1
        else:
            print('nuuuu', server.name, file=open('2.log', 'a'))
            self.cursor = 0
        self.redraw()

    def press(self, key):
        super().press(key)
        if key == 10:
            self.ui.set_channel(self.data[self.cursor])
            self.ui.status.redraw()
            self.ui.pad.redraw()
            self.redraw()


class WinUser(subwin.Win):
    win_name = 'user'


class WinStatus(subwin.Win):
    """Status."""
    win_name = 'status'

    def draw(self):
        """Draw status bar."""
        message = ''
        channel = self.ui.channel
        if self.ui.server is None:
            message = 'DiscordZ - connected as ' + self.ui.client.user.name
        else:
            if self.ui.server.id != 0:
                message = self.ui.server.name + ' '
            if channel is not None:
                if channel.is_private is None:
                    message += '@'
                message += channel.display_name
                if not channel.is_private and channel.topic is not None and len(channel.topic.strip()) > 0:
                    message += ' - '
                    max_length = self.width - len(message)
                    if len(channel.topic) > max_length:
                        self.redraw()
                    message += utils.slide_text(self.ui.channel.topic, max_length, max_length // 3, 0.1)
        self.clear()
        self.addstr(0, 0, message, self.ui.theme.pair('main'))


class WinBox(subwin.Win):
    """Text edit zone."""
    win_name = 'box'

    def __init__(self, window, ui):
        super().__init__(window, ui)
        self.text = curses.textpad.Textbox(self.win)

    def draw(self):
        if self.focused and self.ui.channel is not None:
            curses.curs_set(1)
        else:
            curses.curs_set(0)

    def press(self, key):
        if self.ui.channel is not None:
            if key == 10:
                self.ui.queue(self.ui.client.send_message, self.ui.channel.channel, self.text.gather())
                self.clear()
            else:
                self.text.do_command(key)


class WinPad(subwin.Win):
    """Main chat box."""
    win_name = 'pad'

    def draw(self):
        log = []
        if self.ui.channel is not None:
            log.extend(self.ui.channel.messages[:self.height][::-1])
        self.clear()
        for i, message in enumerate(log):
            auth, serv, text = message.author, message.server, message.content
            name = (auth.nick or auth.name) if isinstance(auth, discord.Member) else auth.name
            self.addstr(i, 0, '%s: %s' % (name, text))
