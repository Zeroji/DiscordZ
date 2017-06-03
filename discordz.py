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
        try:
            window = curses.initscr()
            curses.noecho()
            curses.cbreak()
            window.keypad(1)
            curses.start_color()
            await self.callback(window, thm.Theme(self.theme), self)
        finally:
            if 'window' in locals():
                window.keypad(0)
                curses.echo()
                curses.nocbreak()
                curses.endwin()

FOCUS_SHORTCUTS = {21: 'user', 6: 'serv', 7: 'chan', 8: 'pad', 0: 'box'}


async def main(window, theme, client):
    """Main function."""
    curses.use_default_colors()
    curses.curs_set(0)

    theme.refresh_layout(window)

    key = -1

    win = ui.UI(window, theme, client)
    focus = 'serv' if theme.serv is not None else 'pad'

    while key != ord('q'):
        focus = win.press(key, focus) or focus
        win.draw(focus)
        theme.refresh_windows()
        try:
            key = window.getch()
        except KeyboardInterrupt:
            key = 3
        if key in FOCUS_SHORTCUTS.keys():
            focus = FOCUS_SHORTCUTS[key]
            key = -1


def _run():
    token = open('token').read().strip()
    client = Client(main, 'theme.toml')
    try:
        client.run(token, bot=False)
    except KeyboardInterrupt:
        pass
    except:
        raise
    finally:
        client.logout()

if __name__ == '__main__':
    if os.environ.get('TERM') != 'xterm-256color':
        print('Setting $TERM to `xterm-256color`')
        os.environ['TERM'] = 'xterm-256color'
    _run()
