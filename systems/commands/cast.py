# felt better to have this just a trigger system and put everything that belongs in the fishing cycle into the system file

from systems.logger import debug_on, log
from systems.fishing import fishing

class Cast:
    def __init__(self, client):
        self.client = client
        self.fishing = fishing.Fishing(self.client)

    async def command(self, message):
        log(f'[Fishing] - {message.author} Casting...')
        await self.fishing.cast(message)


