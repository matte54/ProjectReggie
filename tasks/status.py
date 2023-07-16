# Simple little task that changes around woodhouses status to different fun messages

import discord
import asyncio
import random

# make this into a file with hundreds of things, even just normal
# status messages instead of playing i know it can be done.
status_flare = ["with you!", "Civilization", "Minecraft", "Heroin", "Hide and seek"]


class StatusTask:
    def __init__(self):
        pass

    async def status_task(self, client):
        while True:
            await client.wait_until_ready()
            i = random.choice(status_flare)
            await client.change_presence(activity=discord.Game(i))
            await asyncio.sleep(120)
