import json
import os

from systems.logger import log, debug_on
from systems.filemanager import VarManager


class HouseKeeper:
    def __init__(self):
        # startup housekeeping
        self.logrotate()  # rotate chat logs if needed (monthly?)
        self.timefiledelete()  # delete fishing timefiles

    def logrotate(self):
        pass

    def timefiledelete(self):
        pass

    def gatherids(self, client):
        # get all guilds the bot is currently in and add them to a list
        guild_list = []
        for guild in client.guilds:
            guild_list.append(guild)
        # if the ID file already exists, get all users that is not a bot
        # and add them ID is the key and the value is their username str
        if os.path.exists("./data/etc/ids.json"):
            with open("./data/etc/ids.json", "r") as f:
                data = json.load(f)
            for i in guild_list:
                for e in i.members:
                    if not e.bot and str(e.id) not in data:
                        data[str(e.id)] = e.global_name
            self.write_json("./data/etc/ids.json", data)
        else:
            # this is just for when there is no file during first start
            data = {}
            for i in guild_list:
                for e in i.members:
                    if not e.bot:
                        data[str(e.id)] = e.global_name
            self.write_json("./data/etc/ids.json", data)

    def write_json(self, filepath, data):
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
