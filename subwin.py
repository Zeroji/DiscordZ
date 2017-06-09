"""Wrapper around curses.window class."""
import curses
import string
import unicodedata

BLOCK = ('Cn', 'Co', 'Cs')


def check(text):
    """Strip away unprintable Unicode from string."""
    return ''.join([c for c in text if unicodedata.category(c) not in BLOCK])


class Win:
    """Same as curses.windows but with neater attributes."""
    win_name = 'user'

    @classmethod
    def get_rect(cls, theme):
        return theme.get_layout(cls.win_name)

    @classmethod
    def from_rect(cls, ui):
        rect = ui.theme.get_layout(cls.win_name)
        if rect is None:
            return None
        return cls(ui.window.subwin(rect.h, rect.w, rect.y, rect.x), ui)

    def __init__(self, window, ui):
        """Init from window."""
        self.win = window
        self.ui = ui
        self.y, self.x = window.getparyx()
        self.height, self.width = window.getmaxyx()
        self._redraw = True
        self._refresh = False
        self.focused = False

    def __getattr__(self, key):
        """Magic method."""
        return self.win.__getattribute__(key)

    def redraw(self):
        """Mark for redraw."""
        self._redraw = True

    def refresh(self):
        """Refresh window if needed."""
        if not self._refresh:
            return
        self.win.refresh()
        self._refresh = False

    def update_rect(self, theme):
        rect = self.get_rect(theme)
        self.win.mvderwin(rect.y, rect.x)
        self.win.resize(rect.h, rect.w)
        self.win.mvwin(rect.y, rect.x)
        self.y, self.x = self.win.getparyx()
        self.height, self.width = self.win.getmaxyx()
        self.redraw()

    def addstr(self, row, col, string, attr=0):
        """Window.addstr wrapper handling curses.error."""
        try:
            self.win.addstr(row, col, check(string), attr)
        except curses.error:
            pass

    def addlnstr(self, row, col, string, length, attr=0):
        """Window.addnstr wrapper using ljust and handling curses.error."""
        try:
            self.win.addnstr(row, col, check(string).ljust(length), length, attr)
        except curses.error:
            pass

    def press(self, key):
        pass

    def focus_on(self):
        if not self.focused:
            self.redraw()
        self.focused = True
        pass

    def focus_off(self):
        if self.focused:
            self.redraw()
        self.focused = False
        pass

    def draw_(self):
        if not self._redraw:
            return
        self._redraw = False
        self.draw()
        self._refresh = True

    def draw(self):
        self.win.clear()
        self.addstr(0, 0, self.__class__.__name__ + ('focus' if self.focused else 'nope'))
        self.addstr(1, 0, ','.join(map(str, (self.x, self.y, self.width, self.height))))


class WinList(Win):  # Scrollable list of items
    def __init__(self, window, ui):
        super().__init__(window, ui)
        self.data = []
        self.data_to_key = lambda _: _
        self.data_to_text = lambda _: _
        self.display = lambda data, row, sel: self.addlnstr(row, 0, self.data_to_text(data)[:self.width],
                                                            self.width, self.pair_selection if sel else self.pair_main)
        self.cursor = 0
        self.offset = 0
        self.pair_main = 0
        self.pair_selection = 1

    def draw(self):
        self.pair_selection = self.ui.theme.pair('sel_focus' if self.focused else 'sel')
        for i in range(min(self.height, len(self.data) - self.offset)):
            self.display(self.data[i + self.offset], i, i + self.offset == self.cursor)

    def press(self, key):
        old = self.cursor
        old_off = self.offset
        cap = len(self.data) - 1
        if key == 259 and self.cursor > 0:      # Up
            self.cursor -= 1
        if key == 258 and self.cursor < cap:    # Down
            self.cursor += 1
        if key == 262 and self.cursor > 0:      # Home
            self.cursor = 0
        if key == 360 and self.cursor < cap:    # End
            self.cursor = cap
        if key == 337 and self.offset > 0:      # Shift + Up
            self.offset -= 1
        if key == 336 and self.offset < cap - self.height + 1:  # Shift + Down
            self.offset += 1
        try:
            char = chr(key)
        except ValueError:
            pass
        else:
            if char in string.printable and char not in string.whitespace:
                target = [i for (i, x) in enumerate(self.data) if self.data_to_key(x).lower().startswith(char.lower())]
                if len(target) == 1:
                    self.cursor = target[0]
                elif len(target) > 1:
                    if self.cursor in target:
                        current = target.index(self.cursor)
                        nxt = (current + 1) % len(target)
                        self.cursor = target[nxt]
                    else:
                        self.cursor = target[0]
        if self.cursor != old:
            if self.cursor - self.offset >= self.height:
                self.offset = self.cursor - self.height + 1
            if self.cursor - self.offset < 0:
                self.offset = self.cursor
            self.redraw()
        if self.offset != old_off:
            self.redraw()
