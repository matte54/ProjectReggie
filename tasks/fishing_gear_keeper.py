import json
import asyncio
import os
import datetime

from systems.logger import log
from systems.varmanager import VarManager


class FishingGearHandler:
    def __init__(self, client):
        self.client = client
        self.varmanager = VarManager()
        self.fishing_channels = None
        self.profiles_path = "./local/fishing/profiles/"
        self.items_file = "./data/fishing/items.json"
        self.profiles_list = []

    async def check_gear(self):
        await asyncio.sleep(10)
        self.fishing_channels = self.collect_channel_ids()
        log(f'[Fishing Gear Handler] - Starting profile searches')
        while self.client:
            current_time = datetime.datetime.now()
            three_hours_ago = current_time - datetime.timedelta(hours=3)
            self.find_profiles()
            for profile in self.profiles_list:
                user_id = profile.replace(".json", "")
                with open(f'{self.profiles_path}{profile}', "r") as f:
                    profile_data = json.load(f)
                if not profile_data["gear"]:
                    continue
                for item in profile_data["gear"]:
                    if datetime.datetime.fromisoformat(item[1]) < three_hours_ago:
                        # remove item from userprofile
                        profile_data["gear"].remove(item)
                        self.write_json(f'{self.profiles_path}{profile}', profile_data)
                        # reset item status in shop
                        with open(f'{self.items_file}', "r") as f:
                            items_dict = json.load(f)
                            items_dict[item][2] = True
                            self.write_json(f'{self.items_file}', items_dict)
                        # message fishing channels
                        for channel in self.fishing_channels:
                            ch = self.client.get_channel(channel)
                            await ch.send(f'```yaml\n\nRent time expired on {item[0]} for'
                                          f' {self.get_user_name(user_id)}```')
                            await asyncio.sleep(2)

            await asyncio.sleep(60)

    def write_json(self, filepath, data):
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)

    def find_profiles(self):
        self.profiles_list = []
        for root, dirs, files in os.walk(self.profiles_path):
            for file in files:
                self.profiles_list.append(file)

    def collect_channel_ids(self):
        if self.varmanager.read("fishing_channels"):
            fishing_channels = self.varmanager.read("fishing_channels")
            return fishing_channels

    def get_user_name(self, user_id):
        if os.path.exists(f'./data/etc/ids.json'):
            with open(f'./data/etc/ids.json', "r") as f:
                id_data = json.load(f)
            if str(user_id) in id_data:
                return id_data[str(user_id)]
