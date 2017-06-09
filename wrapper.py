import discord


class Common:
    def __init__(self):
        self.focused = False

    def focus_on(self):
        self.focused = True

    def focus_off(self):
        self.focused = False


class Channel(Common):
    """Wrapper around discord.Channel."""
    msg_sort = (lambda m: m.timestamp.timestamp())

    def __init__(self, channel: discord.Channel):
        super(Channel, self).__init__()
        self.channel = channel
        self.messages = []
        self.unread = False
        self.mentions = 0
        self.name = channel.name
        self.display_name = None if channel.name is None else '#' + self.name

    def __getattr__(self, key):
        return self.channel.__getattribute__(key)

    def focus_on(self):
        super(Channel, self).focus_on()
        self.mark_read()

    def mark_read(self):
        self.mentions = 0
        self.unread = 0

    async def update(self, client):
        await self.load_logs(client)

    async def load_logs(self, client, limit=100):
        if len(self.messages) >= limit:
            return
        try:
            async for message in client.logs_from(self, limit=limit):
                self._add_message(message)
        except discord.Forbidden:
            pass
        self.sort_messages()

    def has_message(self, message):
        for m in self.messages:
            if m.id == message.id:
                return True
        return False

    def find_message(self, message):
        for i, m in enumerate(self.messages):
            if m.id == message.id:
                return i
        return -1

    def sort_messages(self):
        self.messages.sort(key=Channel.msg_sort, reverse=True)

    def _add_message(self, message):
        if not self.has_message(message):
            self.messages.append(message)
            return True
        return False

    def add_message(self, message):
        if self._add_message(message):
            self.sort_messages()

    def delete_message(self, message):
        if not self.has_message(message):
            return
        del self.messages[self.find_message(message)]

    def edit_message(self, before, after):
        if not self.has_message(before):
            self.add_message(after)
        else:
            self.messages[self.find_message(before)] = after


class PrivateChannel(Channel):
    """Wrapper around discord.PrivateChannel."""
    def __init__(self, channel: discord.PrivateChannel):
        super().__init__(channel)
        if channel.name is not None:
            self.name = channel.name
        else:
            self.name = ', '.join([user.name for user in channel.recipients])
        self.display_name = self.name


class Server(Common):
    """Wrapper around discord.Server."""
    def __init__(self, server: discord.Server):
        super(Server, self).__init__()
        self.server = server
        self.channels = []
        self.focused_channel = None
        self.default_channel = None

    def __getitem__(self, key):
        for channel in self.channels:
            if channel is key or channel.channel is key or channel.id == key:
                return channel

    def __getattr__(self, key):
        if key == 'mentions':
            return sum([channel.mentions for channel in self.channels])
        elif key == 'unread':
            return any([channel.unread for channel in self.channels])
        else:
            return self.server.__getattribute__(key)

    def mark_read(self):
        for channel in self.channels:
            channel.mark_read()

    async def update(self, client):
        self.channels = [Channel(channel) for channel in self.server.channels if channel.type is discord.ChannelType.text]
        self.channels.sort(key=lambda c: c.position)
        self.default_channel = self.channels[0] if self.server is None else self[self.server.default_channel]


class DirectMessages(Server):
    """Fake server handling all the private channels."""
    def __init__(self, client):
        super(DirectMessages, self).__init__(None)
        self.id = 0
        self.name = 'Friends'
        self.channels = [PrivateChannel(channel) for channel in client.private_channels]
        self.default_channel = self.channels[0]

    async def update(self, client):
        self.channels = [PrivateChannel(channel) for channel in client.private_channels]
        # for channel in self.channels:
        #     if len(channel.messages) == 0:
        #         await channel.load_logs(client, 1)
        # self.channels.sort(key=lambda c: c.messages[0].timestamp, reverse=True)
        self.default_channel = self.channels[0]

