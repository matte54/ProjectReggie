import json
import os
from systems.logger import log
from systems.varmanager import VarManager


class Bucket:
    def __init__(self):
        self.varmanager = VarManager()

    def get_user_name(self, user_id):
        if os.path.exists(f'./data/etc/ids.json'):
            with open(f'./data/etc/ids.json', "r") as f:
                id_data = json.load(f)
            if str(user_id) in id_data:
                return id_data[str(user_id)]

    async def command(self, message):
        if self.varmanager.read("fishing_channels"):
            fishing_channels = self.varmanager.read("fishing_channels")
            if message.channel.id in fishing_channels:
                user_id = str(message.author.id)
                log(f'[Bucket] - {message.author} is listing their bucket')
                try:
                    with open(f'./local/fishing/buckets/{user_id}.json', "r") as f:
                        bucket_data = json.load(f)
                    with open(f'./local/fishing/profiles/{user_id}.json', "r") as f:
                        profile_data = json.load(f)

                        # sort bucket for biggest fish
                        sorted_dict_descending = dict(
                            sorted(bucket_data.items(), key=lambda item: item[1]['weight'], reverse=True))

                        # read profile stats and create string
                        bucket_str = f'-- Lvl: {profile_data["level"]} - Exp: {profile_data["xp"]}/' \
                                     f'{profile_data["xpCap"]} - Bells: {profile_data["money"]} --'

                        bucket_str += f'\n{self.get_user_name(user_id).capitalize()}´S BUCKET(TOP 10)\n'
                        limit = 0
                        for i in sorted_dict_descending:
                            bucket_str += i.upper() + ' - ' + str(sorted_dict_descending[i]["weight"]) + ' LBS\n'
                            limit += 1
                            if limit == 10:
                                break
                        await message.channel.send(f'```yaml\n\n{bucket_str}```')

                except FileNotFoundError:
                    if os.path.exists(f'./local/fishing/profiles/{user_id}.json'):
                        with open(f'./local/fishing/profiles/{user_id}.json', "r") as f:
                            profile_data = json.load(f)

                        bucket_str = f'-- Lvl: {profile_data["level"]} - Exp: {profile_data["xp"]}/' \
                                     f'{profile_data["xpCap"]} - Bells: {profile_data["money"]} --'
                        bucket_str += f'\n{str(message.author).upper()}´S BUCKET(TOP 10)\n'
                        bucket_str += f'empty'
                        await message.channel.send(f'```yaml\n\n{bucket_str}```')
                    else:
                        await message.channel.send(f'```yaml\n\nNo fishing data on this user```')
