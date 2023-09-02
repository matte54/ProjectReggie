# background task that keeps the database of when a person was last online
# for the "seen" command.

import os
import json
import datetime
import asyncio


class SeenSaver:
    def __init__(self, client):
        self.client = client
        self.filepath = "./local/seen.json"
        if not os.path.isfile(self.filepath):
            x = {}
            self.write_json(self.filepath, x)

    async def seen(self):
        await self.client.wait_until_ready()
        while True:
            guild_list = []
            for guild in self.client.guilds:
                guild_list.append(guild)

            with open(self.filepath, "r") as f:
                data = json.load(f)
            for i in guild_list:
                for member in i.members:
                    if not member.bot:
                        if str(member.status) == "online" or str(member.mobile_status) == "online":
                            now = datetime.datetime.now()
                            data[str(member.id)] = now.strftime("%Y-%m-%d %H:%M:%S")

            self.write_json(self.filepath, data)
            await asyncio.sleep(120)

    def write_json(self, filepath, data):
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
