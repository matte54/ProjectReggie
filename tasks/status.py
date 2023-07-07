# Simple little task that changes around woodhouses status to diffrent fun messages

import discord
import asyncio
import random

# make this into a file with hundreds of things, even just normal status messages instead of playing i know it can be done.
status_flare = ["with you!", "Civilization", "Minecraft", "Heroin", "Hide and seek"]


class StatusTask:
    async def status_task(self):
        while True:
            await self.wait_until_ready()
            i = random.choice(status_flare)
            await self.change_presence(activity=discord.Game(i))
            await asyncio.sleep(120)
