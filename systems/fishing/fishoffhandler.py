import json
import os
import datetime
import asyncio

from systems.logger import log
from systems.varmanager import VarManager
from systems.gif_finder import Giphy_find


class Fishoffhandler:
    def __init__(self, client):
        self.client = client
        self.varmanager = VarManager()
        self.gifs = Giphy_find()

        # files and directories
        self.fishoff_file = f"./local/fishing/fishoff.json"
        self.fishoff_history_file = f"./local/fishing/fishoff_history.txt"
        self.challenge_file = f"./local/fishing/challenge.json"  # to be used later
        self.challenge_history_file = f"./local/fishing/challenge_history.txt"  # to be used later
        self.bucket_dir = f"./local/fishing/buckets/"

        # -
        self.now = None
        self.current_month = datetime.datetime.now().strftime('%B %Y')
        self.active_channels = self.collect_channel_ids()  # list of channels with fishing turned on

        # create the history file if there isent one
        if not os.path.exists(self.fishoff_history_file):
            with open(self.fishoff_history_file, 'a', encoding='utf-8'):
                pass

    async def check_date(self):
        self.now = datetime.datetime.now()
        if self.now.day == 1:  # changed for debugging
            with open(self.fishoff_history_file, 'r', encoding='utf-8') as f:
                last_entry = f.readline().strip()
                if last_entry.startswith(self.current_month):
                    log(f'[Fishoff Handler] We already crowned a winner this month')
                    return
            await self.fishoff()
        else:
            log(f'[Fishoff Handler] Day of the month is {self.now.day} keep fishing')

    async def fishoff(self):
        if os.path.exists(f'./local/fishing/fishoff.json'):
            with open(f'./local/fishing/fishoff.json', "r") as f:
                fishoff_data = json.load(f)
            sorted_dict_descending = dict(
                sorted(fishoff_data.items(), key=lambda item: item[1]['weight'], reverse=True))
            winner_dict = next(iter(sorted_dict_descending.values()))
            id_str = next(iter(sorted_dict_descending))
            username_str = self.get_user_name(id_str)

            if winner_dict["shiny"]:
                shiny_str = "*"
            else:
                shiny_str = ""
            winner_str = (f'{self.current_month} - {username_str.capitalize()} - '
                          f'{winner_dict["name"]}{shiny_str} - {winner_dict["weight"]} lbs')

            # do this cause i want the latest winning month on top
            with open(self.fishoff_history_file, 'r') as history_file:
                existing_content = history_file.read()
            with open(self.fishoff_history_file, 'w') as history_file:
                history_file.write(winner_str + '\n' + existing_content)

            gif = self.gifs.find("winner congratulations fish")

            # send message about winner in all active fishing channels
            for channel in self.active_channels:
                ch = self.client.get_channel(channel)
                await ch.send(f'```yaml\n\n- - - - - FISHOFF SEASON END SCORE - - - - -\n'
                              f'{winner_str}```')
                if gif:
                    await ch.send(gif)
                await asyncio.sleep(2)  # slow this down a bit might be rate limited

            self.add_win_stat(id_str)
            self.clear_files()  # delete buckets and fishoff file

        else:
            for channel in self.active_channels:
                ch = self.client.get_channel(channel)
                await ch.send(f'```yaml\n\nNo one ever fished what the hell lul, no winners```')
                await asyncio.sleep(2)

    def challenge(self):
        pass

    def clear_files(self):
        # delete all buckets
        file_list = os.listdir(self.bucket_dir)
        for file_name in file_list:
            file_path = os.path.join(self.bucket_dir, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)
                log(f'[Fishoff Handler] Deleted: {file_path}')
            else:
                log(f'[Fishoff Handler] Skipped (not a file): {file_path}')
        # delete fishoff file
        if os.path.isfile(self.fishoff_file):
            os.remove(self.fishoff_file)
            log(f'[Fishoff Handler] Deleted: {self.fishoff_file}')

    def collect_channel_ids(self):
        if self.varmanager.read("fishing_channels"):
            fishing_channels = self.varmanager.read("fishing_channels")
            return fishing_channels

    def add_win_stat(self, id_str):
        with open(f'./local/fishing/profiles/{id_str}.json', "r") as f:
            profile_data = json.load(f)
        profile_data["wins"] += 1
        self.write_json(f'./local/fishing/profiles/{id_str}.json', profile_data)

    def get_user_name(self, user_id):
        if os.path.exists(f'./data/etc/ids.json'):
            with open(f'./data/etc/ids.json', "r") as f:
                id_data = json.load(f)
            if str(user_id) in id_data:
                return id_data[str(user_id)]

    def write_json(self, filepath, data):
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
