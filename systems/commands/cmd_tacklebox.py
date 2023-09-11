from systems.logger import debug_on, log
from systems.fishing import tacklebox

from systems.varmanager import VarManager
from systems.fishing import tacklebox


class Tacklebox:
    def __init__(self, client):
        self.client = client
        self.tacklebox = tacklebox.Tacklebox(self.client)
        self.varmanager = VarManager()

    async def command(self, message):
        if self.varmanager.read("fishing_channels"):
            fishing_channels = self.varmanager.read("fishing_channels")
            if message.channel.id in fishing_channels:
                await self.tacklebox.process_message(message)
