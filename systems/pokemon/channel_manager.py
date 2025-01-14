from systems.varmanager import VarManager
from systems.logger import log


class ChannelManager:
    def __init__(self, client):
        self.varmanager = VarManager()
        self.pokemon_channels = None
        self.client = client

    async def enable(self, message):
        if self.varmanager.read("pokemon_channels"):
            pokemon_channels = self.varmanager.read("pokemon_channels")
            if message.channel.id in pokemon_channels:
                await message.channel.send(f'```yaml\n\nThis channel already has pokémon enabled```')
                return
            pokemon_channels.append(message.channel.id)
            self.varmanager.write("pokemon_channels", pokemon_channels)
            await message.add_reaction("👍")
            return
        else:
            self.varmanager.write("pokemon_channels", [message.channel.id])
            await message.add_reaction("👍")
            return

    async def disable(self, message):
        if self.varmanager.read("pokemon_channels"):
            pokemon_channels = self.varmanager.read("pokemon_channels")
            if message.channel.id in pokemon_channels:
                pokemon_channels.remove(message.channel.id)
                self.varmanager.write("pokemon_channels", pokemon_channels)
                await message.add_reaction("👍")
                return
            else:
                await message.channel.send(f'```yaml\n\nThis channel is NOT enabled for pokémon```')
                return
        else:
            await message.channel.send(f'```yaml\n\nThere are NO channels enabled for pokémon```')
            return

