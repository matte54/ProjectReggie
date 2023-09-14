# felt better to have this just a trigger system and put everything that belongs in the fishing cycle into the system
# file

from systems.logger import debug_on, log
from systems.fishing import fishing
from systems.varmanager import VarManager


class Cast:
    def __init__(self, client):
        self.client = client
        self.fishing = fishing.Fishing(self.client)
        self.varmanager = VarManager()

    async def command(self, message):
        if self.varmanager.read("fishing_channels"):
            fishing_channels = self.varmanager.read("fishing_channels")
            if message.channel.id in fishing_channels:
                log(f'[Fishing] - {message.author} is CASTING their line!')
                await self.fishing.cast(message)
