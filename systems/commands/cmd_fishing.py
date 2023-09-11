# this command enables puts whatever channel this is typed in into a variable
# plan is to have all fishing related commands and automatic messages only be posted and able
# to be executed in those channels. ie casting, checking stats, also winner messages etc should only be posted there

from systems.varmanager import VarManager
from systems.logger import log
from data.etc.admins import ADMINS


class Fishing:
    def __init__(self):
        self.varmanager = VarManager()
        self.fishing_channels = None
        self.admins = ADMINS

    async def command(self, message):
        if message.author.id in self.admins:
            msg = message.content.replace("$fishing ", "")
            log(f'[Fishing] - {message.author} - {msg}')
            if msg == "on":
                if self.varmanager.read("fishing_channels"):
                    fishing_channels = self.varmanager.read("fishing_channels")
                    if message.channel.id in fishing_channels:
                        await message.channel.send(f'```yaml\n\nThis channel already has fishing on```')
                        return
                    fishing_channels.append(message.channel.id)
                    self.varmanager.write("fishing_channels", fishing_channels)
                    await message.add_reaction("👍")
                    return
                else:
                    self.varmanager.write("fishing_channels", [message.channel.id])
                    await message.add_reaction("👍")
                    return
            elif msg == "off":
                if self.varmanager.read("fishing_channels"):
                    fishing_channels = self.varmanager.read("fishing_channels")
                    if message.channel.id in fishing_channels:
                        fishing_channels.remove(message.channel.id)
                        self.varmanager.write("fishing_channels", fishing_channels)
                        await message.add_reaction("👍")
                        return
                    else:
                        await message.channel.send(f'```yaml\n\nThis channel is NOT enabled for fishing```')
                        return
                else:
                    await message.channel.send(f'```yaml\n\nThere are NO channels enabled for fishing```')
                    return
            else:
                await message.channel.send(f'```yaml\n\nError, this command only responds to on/off```')
        else:
            await message.channel.send(f'```yaml\n\nSorry this is a admin-only command```')
