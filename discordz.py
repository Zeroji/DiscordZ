#!/usr/bin/env python3
"""Discord app."""
import asyncio
import curses
import os
import subprocess

import discord
import requests

import theme as thm
import ui as UI


class Client(discord.Client):
    """Wrapper around discord.Client class."""

    def __init__(self, callback, theme):
        super(Client, self).__init__()
        self.callback = callback
        self.theme = theme
        self.ui = None

    def set_ui(self, ui):
        """UI setter."""
        self.ui = ui

    def chan(self, message):
        """Return the wrapper.Channel object of a message."""
        if self.ui is None:
            return None
        if message.channel.is_private:
            server = self.ui.servers[0]
        else:
            server = self.ui.servers.get(message.server.id)
        if server is None:
            return None
        return server[message.channel.id]

    async def on_message(self, message):
        """Add message to channel and handle mentions."""
        # Download avatar to cache
        asyncio.get_event_loop().run_in_executor(None, download_avatar, message.author)

        chan = self.chan(message)
        if chan is None:
            return
        print(message.author.name, message.content, file=open('log', 'a'))
        chan.add_message(message)
        if chan == self.ui.channel:
            self.ui.pad.redraw()
        else:
            mentioned = False
            # Direct mentions
            if any([member for member in message.mentions if member.id == self.user.id]):
                mentioned = True
            # Role mentions
            if message.server is not None:
                roles = message.server.get_member(self.user.id).roles
                if any([r in roles for r in message.role_mentions]):
                    mentioned = True
            # @everyone / @here mentions
            if '@everyone' in message.content or '@here' in message.content:
                mentioned = True
            # Direct messages
            if message.channel.is_private:
                mentioned = True
            if mentioned and message.author.id != self.user.id:
                chan.mentions += 1
                # Desktop notifications (Linux only)
                subprocess.Popen(['notify-send',
                                  '-i', '/tmp/%s.png' % message.author.avatar,
                                  message.author.name, message.clean_content])
            # If we're currently focusing the server in which the message happened
            if self.ui.server is not None and ((message.server is None and self.ui.server.id == 0) or
                                               (message.server is not None and message.server.id == self.ui.server.id)):
                self.ui.chan.redraw()
            self.ui.serv.redraw()
            chan.unread = True
        self.ui.draw()
        self.ui.refresh()

    async def on_message_delete(self, message):
        """Delete message from channel."""
        chan = self.chan(message)
        if chan is None:
            return
        chan.delete_message(message)
        if chan == self.ui.channel:
            self.ui.pad.redraw()
            self.ui.draw()
            self.ui.refresh()

    async def on_message_edit(self, before, after):
        """Edit message in channel."""
        chan = self.chan(before)
        if chan is None:
            return
        chan.edit_message(before, after)
        if chan == self.ui.channel:
            self.ui.pad.redraw()
            self.ui.draw()
            self.ui.refresh()

    async def on_ready(self):
        """Discord client initialization, main function wrapper."""
        window = None
        try:
            window = curses.initscr()
            curses.noecho()         # Don't echo input
            curses.raw()            # Catch Ctrl+S, Ctrl+Z and such
            window.keypad(True)     # Catch Ctrl+Down as one key
            curses.start_color()    # Custom colors
            await self.callback(window, thm.Theme(self.theme), self)
        finally:
            if window is not None:
                window.keypad(False)
                curses.echo()
                curses.nocbreak()
                curses.endwin()
            await self.logout()


def download_avatar(user):
    """Download a user's avatar to /tmp/ if not already done."""
    filename = '/tmp/%s.png' % user.avatar
    if os.path.exists(filename):
        return
    url = user.avatar_url or user.default_avatar_url
    url = url.replace('.webp', '.png')
    file = requests.get(url)
    open(filename, 'wb').write(file.content)


def getch(window):
    """Return the key pressed."""
    key = -1
    while key == -1:
        try:
            key = window.getch()
        except KeyboardInterrupt:
            key = 3
    return key


async def main(window, theme, client):
    """Main function."""
    curses.use_default_colors()
    curses.curs_set(0)

    theme.refresh_layout(window)

    key = -1

    win = UI.UI(window, theme, client)
    await win.update()
    client.set_ui(win)

    while key != 17:  # Ctrl+Q
        if key != -1:
            win.press(key)
        await win.do()  # Queue
        win.draw()
        win.refresh()
        # Blocking for a key press, but letting discord.py run
        key = await asyncio.get_event_loop().run_in_executor(None, getch, window)


def _run():
    token = open('token').read().strip()
    client = Client(main, 'theme.toml')
    try:
        client.run(token, bot=False)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    # Set environment variable
    if os.environ.get('TERM') != 'xterm-256color':
        print('Setting $TERM to `xterm-256color`')
        os.environ['TERM'] = 'xterm-256color'
    # Set terminal title
    print('\33]0;DiscordZ\a', end='')
    _run()
