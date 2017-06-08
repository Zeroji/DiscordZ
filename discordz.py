#!/usr/bin/env python3
"""Discord app."""
import curses
import os
import discord
import theme as thm
import ui


class Client(discord.Client):
    """Wrapper around discord.Client class."""

    def __init__(self, callback, theme):
        super(Client, self).__init__()
        self.callback = callback
        self.theme = theme

    async def on_ready(self):
        """Discord client initialization, main function wrapper."""
        window = None
        try:
            window = curses.initscr()
            curses.noecho()         # Don't echo input
            curses.raw()            # Catch Ctrl+S, Ctrl+Z and such
            window.keypad(True)     # Catch Ctrl+Down as one key
            window.nodelay(True)    # Non-blocking getch()
            curses.start_color()    # Custom colors
            await self.callback(window, thm.Theme(self.theme), self)
        finally:
            if window is not None:
                window.keypad(False)
                curses.echo()
                curses.nocbreak()
                curses.endwin()
            await self.logout()


async def main(window, theme, client):
    """Main function."""
    curses.use_default_colors()
    curses.curs_set(0)

    theme.refresh_layout(window)

    key = -1

    win = ui.UI(window, theme, client)

    while key != 17:  # Ctrl+Q
        if key != -1:
            win.press(key)
        win.draw()
        win.refresh()
        try:
            key = window.getch()
        except KeyboardInterrupt:
            key = 3


def _run():
    token = open('token').read().strip()
    client = Client(main, 'theme.toml')
    try:
        client.run(token, bot=False)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    if os.environ.get('TERM') != 'xterm-256color':
        print('Setting $TERM to `xterm-256color`')
        os.environ['TERM'] = 'xterm-256color'
    _run()
