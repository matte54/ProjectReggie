# Simple little task that changes around woodhouses status to different fun messages

import json
import discord
import asyncio
import random

from systems.logger import log



class StatusTask:
    def __init__(self):
        self.playing = []
        self.watching = []
        self.listening = []
        self.nothing = ["something"]

    async def status_task(self, client):
        while True:
            await asyncio.sleep(10)
            self.load_statuses()

            picked_status_list = random.choice([self.playing, self.listening, self.watching, self.nothing])

            if picked_status_list is self.playing:
                picked_status = random.choice(self.playing)
                await client.change_presence(activity=discord.Game(picked_status))

            if picked_status_list is self.listening:
                picked_status = random.choice(self.listening)
                await client.change_presence(
                    activity=discord.Activity(type=discord.ActivityType.listening, name=picked_status))

            if picked_status_list is self.watching:
                picked_status = random.choice(self.watching)
                await client.change_presence(
                    activity=discord.Activity(type=discord.ActivityType.watching, name=picked_status))

            if picked_status_list is self.nothing:
                picked_status = random.choice(self.nothing)
                await client.change_presence(
                    activity=discord.Activity(type=discord.ActivityType.custom, name=picked_status))

            await asyncio.sleep(3600 + random.randint(-1000, 1000))

    def load_statuses(self):
        self.playing = []
        self.watching = []
        self.listening = []
        with open("./data/etc/default_statuses.json", "r") as f:
            default_status_dict = json.load(f)
        with open("./data/etc/statuses.json", "r") as f:
            user_status_dict = json.load(f)
        # load default ones
        for i in default_status_dict["playing"]:
            self.playing.append(default_status_dict["playing"][i])
        for i in default_status_dict["watching"]:
            self.watching.append(default_status_dict["watching"][i])
        for i in default_status_dict["listening"]:
            self.listening.append(default_status_dict["listening"][i])
        # load user statuses
        user_entries = 0
        for i in user_status_dict["playing"]:
            self.playing.append(user_status_dict["playing"][i])
            user_entries += 1
        for i in user_status_dict["watching"]:
            self.watching.append(user_status_dict["watching"][i])
            user_entries += 1
        for i in user_status_dict["listening"]:
            self.listening.append(user_status_dict["listening"][i])
            user_entries += 1
        log(f'[Status] - Loaded {user_entries} user entries')






