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

        self.user_stats_path = "./local/statistics/user/"
        self.guild_stats_path = "./local/statistics/guild/"
        self.idlist_path = "./data/etc/ids.json"
        self.emojilist_path = "./local/emojis.json"
        self.default_emojis_path = "./data/etc/default_emojis.txt"
        self.gif_find = Giphy_find()

    def logrotate(self):
        file_list = []
        for root, dirs, files in os.walk("./log/"):
            for file in files:
                file_path = os.path.join(root, file)
                file_list.append(file_path)

        for logfile in file_list:
            size = os.path.getsize(logfile)
            size_in_mb = round(size / (1024 * 1024), 1)
            if size_in_mb >= 2.0:  # rotate log if over 2mb
                try:
                    today = datetime.date.today()
                    os.rename(logfile, f'{logfile}{today.strftime("%Y_%m")}')  # rename file with y and d
                    log(f'[Housekeeper] - Rotating log {logfile[6:]}')
                except OSError as e:
                    log(f"Error rotating {logfile[6:]}: {e}")

    def check_monthly_stats(self):
        # reset month section on all stat files if its the first of the month
        now = datetime.datetime.now()
        if now.day == 1:
            log(f'[Housekeeper] - Resetting monthly statistics')
            # user files
            user_file_list = os.listdir(self.user_stats_path)
            for file in user_file_list:
                with open(f"{self.user_stats_path}{file}", "r") as f:
                    data = json.load(f)
                data["month"]["messages"] = 0
                data["month"]["emojis"] = {}
                self.write_json(f"{self.user_stats_path}{file}", data)

            # guild files
            guild_file_list = os.listdir(self.guild_stats_path)
            for file in guild_file_list:
                with open(f"{self.guild_stats_path}{file}", "r") as f:
                    data = json.load(f)
                data["month"]["messages"] = 0
                data["month"]["emojis"] = {}
                data["month"]["users"] = {}
                self.write_json(f"{self.guild_stats_path}{file}", data)

            # fishing stats reset
            with open(f"./local/fishing/stats.json", "r") as f:
                fishdata = json.load(f)
                fishdata["month"]["fails"] = 0
                fishdata["month"]["catches"] = 0
                fishdata["month"]["shinies"] = 0
                fishdata["month"]["uniques"] = 0
                self.write_json(f"./local/fishing/stats.json", fishdata)

    def gather_emojis(self):
        data = {}
        # add in some of the default emojis from the default_emojis file
        default_emoji_list = []
        with open(self.default_emojis_path, "r", encoding='UTF-8') as f:
            default_emoji_list += f.read().splitlines()
        data["default"] = default_emoji_list
        # gather emoji str names in a list and save the in a guild id key
        for guild in self.client.guilds:
            log(f'[Housekeeper] - Saving {guild.name} emojilist')
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
                        if e.name or e.global_name:
                            if e.global_name:
                                data[str(e.id)] = e.global_name
                                log(f'[Housekeeper] - Found new user, saving {e.global_name}')
                            else:
                                data[str(e.id)] = e.name
                                log(f'[Housekeeper] - Found new user, saving {e.name}')
                        else:
                            log(f'[Housekeeper] - Invalid username {e.id}(old account), skipping...')
            self.write_json(self.idlist_path, data)
        else:
            # this is just for when there is no file during first start
            data = {}
            for i in guild_list:
                for e in i.members:
                    if not e.bot:
                        try:
                            data[str(e.id)] = e.global_name
                        except AttributeError:
                            data[str(e.id)] = e.name
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
                    log(f'[Housekeeper] - Today is {i}s cakeday in {guild.name}')
                    main_channel = guild.text_channels[0]
                    await main_channel.send(f'Happy Cakeday {i.mention}')
                    gif = self.gif_find.find("cake birthday")
                    if gif:
                        await main_channel.send(gif)

    def clean_logs(self):
        # cleanup log files (remove empty lines)
        file_paths = []
        for root, dirs, files in os.walk("./log/"):
            for file in files:
                file_path = os.path.join(root, file)
                file_paths.append(file_path)
        for logfile in file_paths:
            # Create a list to store non-empty lines
            updated_lines = []
            lines_removed = False  # Flag to track if any lines were removed

            with open(logfile, "r", encoding='UTF-8') as f:
                for line in f:
                    if not line.strip():
                        lines_removed = True
                    else:
                        updated_lines.append(line.strip())

            # Check if any lines were removed before writing back to the file
            if lines_removed:
                log(f'[Housekeeper] - Cleaning {logfile[6:]}')
                with open(logfile, 'w', encoding='UTF-8') as f:
                    f.write('\n'.join(updated_lines))

    def write_json(self, filepath, data):
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
