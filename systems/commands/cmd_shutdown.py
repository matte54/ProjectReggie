import sys
import asyncio

from systems.logger import log
from data.etc.admins import MATTE


class Shutdown:
    def __init__(self):
        self.matte = MATTE

    async def command(self, message):
        if message.author.id in self.matte:
            log(f'[Shutdown] - Manual shutdown in 10 seconds')
            await message.channel.send(f'```yaml\n\nInitiating remote manual shutdown in 10 seconds...```')
            await asyncio.sleep(10)
            sys.exit()
