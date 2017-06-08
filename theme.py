"""Theme handler for DiscordZ."""
import curses
import toml
import utils

VERT = ('left', 'right')
HOR = ('top', 'bottom')
LOCS = VERT + HOR
INV = {'left': 'right', 'right': 'left', 'top': 'bottom', 'bottom': 'top'}

PAIRS = {'main': ('main', 'background'),
         'sel': ('selection', 'selection_background'),
         'sel_focus': ('selection', 'selection_background_focused')}


def log(*x):
    """Log."""
    with open('out', 'a') as logs:
        logs.write(' '.join([str(e) for e in x]) + '\n')


class Rect:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def set(self, x, y, w, h):
        self.setXY(x, y)
        self.setWH(w, h)

    def setXY(self, x, y):
        self.x = x
        self.y = y

    def setWH(self, w, h):
        self.w = w
        self.h = h


class Theme(object):
    """Define a theme."""

    THEME_ATTR_BLACKLIST = ('force_hex', 'color')

    def __init__(self, data):
        if isinstance(data, str):
            if data.endswith('.toml'):
                with open(data) as toml_file:
                    data = toml_file.read()
                    print(data)
            if data.startswith('#'):
                data = toml.loads(data)
                print(data)
        if not isinstance(data, dict):
            raise TypeError

        data['layout']['borders'] = int(data['layout']['borders'])
        external_data = {}
        for key, value in data.items():
            if key not in self.THEME_ATTR_BLACKLIST:
                external_data[key] = value
        self.external_data = utils.DotMap(external_data)

        curses.use_default_colors()
        self.hex = False
        if curses.can_change_color():
            self.hex = data['force_hex']
            if not self.hex:
                for value in data['color'].values():
                    if (isinstance(value, str) and
                            len(value) == 7 and value[0] == '#'):
                        self.hex = True

        self._colors = {}
        self._customs = 17
        self._pairs = {}
        self.boxes = {}

        for key, value in data['color'].items():
            code = self._process(value)
            self._colors[key] = code

        for key, (fore, back) in PAIRS.items():
            self.pair(fore, back, key)

    def refresh_layout(self, window):
        """Refresh window layout."""
        window.bkgd(self.chars.background, self.pair('main'))
        layout = self.external_data.layout
        attr = {}
        for box in layout.order:
            if box in dir(self):
                self.__delattr__(box)
        scr_x, scr_y = 0, 0
        height, width = window.getmaxyx()
        for box_name in layout.order[:-1]:
            box = layout[box_name]
            if box.location not in LOCS or not box.show:
                attr[box_name] = None
            else:
                if box.location in HOR:
                    win_w = width
                    win_h = box.size
                    win_x = 0
                    win_y = 0 if box.location == 'top' else height - win_h
                    height -= win_h + layout.borders
                else:
                    win_w = box.size
                    win_h = height
                    win_x = 0 if box.location == 'left' else width - win_w
                    win_y = 0
                    width -= win_w + layout.borders
                win_x += scr_x
                win_y += scr_y
                if box_name in attr.keys():
                    attr[box_name].set(win_x, win_y, win_w, win_h)
                else:
                    attr[box_name] = Rect(win_x, win_y, win_w, win_h)
                if box.location == 'left':
                    scr_x += win_w + layout.borders
                elif box.location == 'top':
                    scr_y += win_h + layout.borders
        box_name = layout.order[-1]
        if box_name in attr.keys():
            attr[box_name].set(scr_x, scr_y, width, height)
        else:
            attr[box_name] = Rect(scr_x, scr_y, width, height)
        self.boxes = attr

    def get_layout(self, box_name):
        return self.boxes.get(box_name)

    def borders(self, window):
        """Draw window borders."""
        if not self.borders:
            return
        clr = self.pair('borders', 'background', 'border_color')
        boxes = []
        boxch = self.chars.box
        for box_name in self.layout.order:
            box = self.boxes.get(box_name)
            if box is not None:
                boxes.append((box, self.layout[box_name]))
        boxes = boxes[:-1]
        for i, (win, box) in enumerate(boxes):
            horizontal = box.location in HOR
            other = VERT if horizontal else HOR
            border = boxch.hor if horizontal else boxch.vert
            tee = boxch[box.location[0] + 'tee']

            def get_z(win, box):
                if box.location in HOR:
                    z = (win.y - 1 if box.location == 'bottom' else
                         win.y + win.h)
                else:
                    z = (win.x - 1 if box.location == 'right' else
                         win.x + win.w)
                return z
            box_z = get_z(win, box)

            for z in range(win.w if horizontal else win.h):
                x, y = z + win.x, box_z
                if not horizontal:
                    x, y = y, z + win.y
                window.addstr(y, x, border, clr)

            for win2, box2 in boxes[i + 1:]:
                if box2.location == box.location:
                    break
                if box2.location in other:
                    box2_z = get_z(win2, box2)
                    if horizontal:
                        window.addstr(box_z, box2_z, tee, clr)
                    else:
                        window.addstr(box2_z, box_z, tee, clr)

    def _process(self, value):
        """Process a value from theme.json and returns the color code."""
        if self.hex:
            try:
                code = int(value)
            except ValueError:
                pass
            else:
                if code > 15:
                    raise ValueError('Using extended color along with hex')
        # Quick note about extended color codes:
        # 0-7 are standard, binary: 0bBGR with 0% or 68% color
        # 8-15 are somehow standard, binary: 0bBGR with 0% or 100% color
        # 16-231 are RGB with components between 0 and 5 (216 values)
        # 232-255 are B&W colors from black to white (24 values)
        code = utils.color(value)
        if code is None or code > 15:
            if code is None:
                red, green, blue = utils.colorx(value)
            elif code < 232:
                code = code - 16
                red, green, blue = code // 36, (code % 36) // 6, code % 6
                red, green, blue = [x * 1000 // 6 for x in (red, green, blue)]
            else:
                red, green, blue = [(code - 232) * 1000 // 23] * 3
            code = self.add_rgb(red, green, blue)
        return code

    def __getattr__(self, key):
        """Hacky way to use stuff."""
        return self.external_data[key]

    def add_rgb(self, red, green, blue):
        """Add RGB color to theme palette. Components up to 1000."""
        curses.init_color(self._customs, red, green, blue)
        self._customs += 1
        return self._customs - 1

    def color(self, name):
        """Return the color pair corresponding to name."""
        return self._colors[name]

    def pair(self, fore, back=None, name=None):
        """Return the color pair with foreground and background."""
        if name is not None:
            key = name
        elif back is None:
            key = fore
        else:
            key = (fore, back)
        if key not in self._pairs.keys():
            pair = len(self._pairs) + 1
            if pair < curses.COLOR_PAIRS:
                curses.init_pair(pair, self._colors[fore], self._colors[back])
                self._pairs[key] = pair
        return curses.color_pair(self._pairs[key])

    def mention(self, name):
        """Return the color pair (name, mention_background)."""
        return self.pair(name, 'mention_background')
