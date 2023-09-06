from systems.urlhandler import Urlhandler
from systems.logger import log
class Url:
    def __init__(self, client):
        self.client = client
        self.urlhandler = Urlhandler(self.client)

    async def command(self, message):
        user_id = message.author.id
        url = await self.urlhandler.get_url(None, user_id)

        await message.channel.send(url)