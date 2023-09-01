import json
import os
import datetime

from systems.logger import log, debug_on
from systems.varmanager import VarManager
from systems.gif_finder import Giphy_find


class HouseKeeper:
    def __init__(self, client):
        self.client = client
        # startup housekeeping
        self.logrotate()  # rotate chat logs if needed (monthly?)
        self.idlist_path = "./data/etc/ids.json"
        self.emojilist_path = "./local/emojis.json"
        self.default_emojis_path = "./data/etc/default_emojis.txt"
        self.gif_find = Giphy_find()

    def logrotate(self):
        pass

    def clear_monthly(self):
        # Clear monthly stats and post here?
        pass

    def gather_emojis(self):
        data = {}
        # add in some of the default emojis from the default_emojis file
        default_emoji_list = []
        with open(self.default_emojis_path, "r", encoding='UTF-8') as f:
            default_emoji_list += f.read().splitlines()
        data["default"] = default_emoji_list
        # gather emoji str names in a list and save the in a guild id key
        for guild in self.client.guilds:
            emoji_list = []
            emojis = guild.emojis
            for emoji in emojis:
                emoji_list.append(str(emoji))
            data[str(guild.id)] = emoji_list
        self.write_json(self.emojilist_path, data)

    def gatherids(self):
        # get all guilds the bot is currently in and add them to a list
        guild_list = []
        for guild in self.client.guilds:
            guild_list.append(guild)
        # if the ID file already exists, get all users that is not a bot
        # and add them ID is the key and the value is their username str
        if os.path.exists(self.idlist_path):
            with open(self.idlist_path, "r") as f:
                data = json.load(f)
            for i in guild_list:
                for e in i.members:
                    if not e.bot and str(e.id) not in data:
                        print(e)
                        print(e.global_name, e.name)
                        if not e.global_name:
                            data[str(e.id)] = e.name
                        else:
                            data[str(e.id)] = e.global_name
            self.write_json(self.idlist_path, data)
        else:
            # this is just for when there is no file during first start
            data = {}
            for i in guild_list:
                for e in i.members:
                    if not e.bot:
                        if not e.global_name:
                            data[str(e.id)] = e.name
                        else:
                            data[str(e.id)] = e.global_name
            self.write_json(self.idlist_path, data)

    async def cakeday(self):
        # check cakeday for members
        today = datetime.datetime.now()
        # check each guild woodhouse is in
        for guild in self.client.guilds:
            member_list = []
            # find all members in the guild and add them to a list
            for member in guild.members:
                if not member.bot:
                    member_list.append(member)
            for i in member_list:
                date = i.joined_at
                # check if today is the cakeday
                if date.month == today.month and date.day == today.day:
                    log(f'[Housekeeper] - Today is {i}s cakeday in {guild}')
                    main_channel = guild.text_channels[0]
                    await main_channel.send(f'Happy Cakeday {i.mention}')
                    gif = self.gif_find.find("cake birthday")
                    if gif:
                        await main_channel.send(gif)

    def write_json(self, filepath, data):
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
        if debug_on():
            log(f'[Housekeeper] - Wrote {filepath}')
