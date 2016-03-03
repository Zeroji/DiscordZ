"""Wrapper around curses.window class."""
import curses
import unicodedata

BLOCK = ('Cn', 'Co', 'Cs')


def check(text):
    """Strip away unprintable Unicode from string."""
    return ''.join([c for c in text if unicodedata.category(c) not in BLOCK])


class Win():
    # Also handles all about messages.
    """Same as curses.windows but with neater attributes."""

    def __init__(self, window):
        """Init from window."""
        self.win = window
        self.y, self.x = window.getparyx()
        self.height, self.width = window.getmaxyx()
        self.redraw = True
        self.offset = 0
        self.cursor = 0
        self.length = 0

    def __getattr__(self, key):
        """Magic method."""
        self.redraw = True
        return self.win.__getattribute__(key)

    def refresh(self):
        """Refresh window if needed."""
        if not self.redraw:
            return
        self.win.refresh()

    def addstr(self, row, col, string, attr=0):
        """Window.addstr wrapper handling curses.error."""
        try:
            self.win.addstr(row, col, check(string), attr)
        except curses.error:
            pass

    def addlnstr(self, row, col, string, length, attr=0):
        """Window.addnstr wrapper using ljust and handling curses.error."""
        try:
            self.win.addnstr(row, col, check(string).ljust(length),
                             length, attr)
        except curses.error:
            pass
