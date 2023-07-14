import json
from systems.logger import log, debug_on, write_json


class HouseKeeper:
    def __init__(self):
        pass

    def logrotate():
        pass

    def timefiledelete():
        pass

    def gatherids(self):
        # get all guilds the bot is currently in and add them to a list
        guild_list = []
        for guild in self.guilds:
            guild_list.append(guild)
        # get all users that is not a bot
        for i in guild_list:
            for e in i.members:
                if not e.bot:
                    # now add this to a dict within a dict to a file and write_json
                    print(e.global_name)
                    print(e.id)

