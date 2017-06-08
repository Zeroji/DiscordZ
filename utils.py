"""Various utility functions."""
from collections import OrderedDict
from inspect import ismethod
import time
import discord


def contains_hex(dictionary):
    """Check if a theme object contains hex codes."""
    for value in dictionary.values():
        if isinstance(value, type(dictionary)):
            if contains_hex(value):
                return True
        elif isinstance(value, str):
            if len(value) == 7 and value[0] == '#':
                return True
    return False


def color(code):
    """Return a ncurses color code from a string."""
    if isinstance(code, str):
        if code[0] == '#':
            if len(code) == 7:
                return None  # Tells program to change color
            red, green, blue = [int(c) for c in code[1:4]]
            return red * 36 + green * 6 + blue + 16
        elif code[0] == 'G':
            return 16 + 216 + int(code[1:])
    return int(code)


def colorx(hexcode):
    """Return the r, g, b components, from 0 to 1000."""
    if hexcode[0] == '#':
        hexcode = hexcode[1:]
    return [int(hexcode[i:i+2], 16) * 1000 // 255 for i in range(0, 6, 2)]


def channel_name(channel: discord.Channel):
    """Get display name of a private/group/public channel."""
    if isinstance(channel, discord.PrivateChannel):
        if channel.name is not None:
            return channel.name
        else:
            return ', '.join([user.name for user in channel.recipients])
    else:
        return '#' + channel.name


def slide_text(text, max_length, space=-1, speed=0.2):
    """Fancy horizontal text-scrolling for small spaces."""
    if len(text) <= max_length:
        return text
    if space == -1:
        space = max_length
    total = len(text) + space
    text = text + ' ' * space + text
    return text[int(time.time()//speed) % total:][:max_length]


class DotMap(OrderedDict):
    """Ordered, dynamically-expandable dot-access dictionary.

    Written by Chris Redford
    https://github.com/drgrib/dotmap
    https://pypi.python.org/pypi/dotmap/1.1.2

    Cleaned to respect conventions.
    Shortened to useful parts.
    """

    # pylint: disable=W0231,R0201,E1101
    def __init__(self, *args, **kwargs):
        self._map = OrderedDict()
        if args:
            data = args[0]
            if isinstance(data, dict):
                for key, val in self.__call_items(data):
                    if isinstance(val, dict):
                        val = DotMap(val)
                    self._map[key] = val
        if kwargs:
            for key, val in self.__call_items(kwargs):
                self._map[key] = val

    def __call_items(self, obj):
        if hasattr(obj, 'iteritems') and ismethod(getattr(obj, 'iteritems')):
            return obj.iteritems()
        else:
            return obj.items()

    def __getitem__(self, k):
        if k not in self._map:
            # automatically extend to new DotMap
            self[k] = DotMap()
        return self._map[k]

    def __getattr__(self, key):
        if key == '_map':
            super(DotMap, self).__getattr__(key)
        else:
            return self[key]

    def __str__(self):
        items = []
        for key, val in self.__call_items(self._map):
            items.append('{0}={1}'.format(key, repr(val)))
        out = 'DotMap({0})'.format(', '.join(items))
        return out

    def __repr__(self):
        return str(self)
