import json
import os
import datetime
from systems.logger import log
from systems.varmanager import VarManager



class Fishoff:
    def __init__(self):
        self.varmanager = VarManager()

    async def command(self, message):
        if self.varmanager.read("fishing_channels"):
            fishing_channels = self.varmanager.read("fishing_channels")
            if message.channel.id in fishing_channels:
                log(f'[Fishoff] - {message.author} is listing fishoff score')

                if os.path.exists(f'./local/fishing/fishoff.json'):
                    with open(f'./local/fishing/fishoff.json', "r") as f:
                        fishoff_data = json.load(f)

                    # sort for biggest fish
                    sorted_dict_descending = dict(
                        sorted(fishoff_data.items(), key=lambda item: item[1]['weight'], reverse=True))
                    current_month = datetime.datetime.now().strftime('%B %Y')
                    fishoff_str = f'\n- - - - FISHOFF SCORES {current_month.upper()} - - - -\n'

                    placenumber = 1
                    for i in sorted_dict_descending:
                        username = self.get_user_name(i)
                        if sorted_dict_descending[i]["shiny"]:
                            shiny_str = "*"
                        else:
                            shiny_str = ""
                        fishoff_str += f'{placenumber} - {username.capitalize()} - {str(sorted_dict_descending[i]["name"])}{shiny_str} - {str(sorted_dict_descending[i]["weight"])} lbs\n'
                        placenumber += 1
                    await message.channel.send(f'```yaml\n\n{fishoff_str}```')
                else:
                    await message.channel.send(f'```yaml\n\nNo fishing data on this user```')

    def get_user_name(self, user_id):
        if os.path.exists(f'./data/etc/ids.json'):
            with open(f'./data/etc/ids.json', "r") as f:
                id_data = json.load(f)
            if str(user_id) in id_data:
                return id_data[str(user_id)]