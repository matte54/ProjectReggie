# Simple little task that changes around woodhouses status to different fun messages

import discord
import asyncio
import random

from data.etc.statuses import GAMES, LISTENING, WATCHING, MESSAGE

class StatusTask:
    def __init__(self):
        self.games = GAMES
        self.listening = LISTENING
        self.watching = WATCHING
        self.message = MESSAGE

    async def status_task(self, client):
        while True:
            await client.wait_until_ready()

            picked_status_list = random.choice([self.games, self.listening, self.watching, self.message])

            if picked_status_list is self.games:
                picked_status = random.choice(self.games)
                await client.change_presence(activity=discord.Game(picked_status))

            if picked_status_list is self.listening:
                picked_status = random.choice(self.listening)
                await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=picked_status))

            if picked_status_list is self.watching:
                picked_status = random.choice(self.watching)
                await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=picked_status))


            # this seems broken for now might need more then a str for custom?
            if picked_status_list is self.message:
                picked_status = random.choice(self.message)
                await client.change_presence(activity=discord.Activity(type=discord.ActivityType.custom, name=picked_status))

            await asyncio.sleep(120)
