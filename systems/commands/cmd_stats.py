import json
import os
import re
from systems.logger import log
from systems.varmanager import VarManager


class Stats:
    def __init__(self):
        self.varmanager = VarManager()
        self.re_pattern = re.compile(r'<:(.*?):')

    def get_user_name(self, user_id):
        if os.path.exists(f'./data/etc/ids.json'):
            with open(f'./data/etc/ids.json', "r") as f:
                id_data = json.load(f)
            if str(user_id) in id_data:
                return id_data[str(user_id)]

    async def command(self, message):
        user_id = str(message.author.id)
        username = self.get_user_name(user_id)
        log(f'[Stats] - {message.author} is listing their stats')
        try:
            with open(f'./local/statistics/user/{user_id}.json', "r") as f:
                user_data = json.load(f)

            # sort monthly emojis
            m_emojis_dict = user_data["month"]["emojis"]
            monthly_sorted_dict_descending = dict(sorted(m_emojis_dict.items(), key=lambda x: x[1], reverse=True))

            # sort alltime emojis
            a_emojis_dict = user_data["alltime"]["emojis"]
            alltime_sorted_dict_descending = dict(sorted(a_emojis_dict.items(), key=lambda x: x[1], reverse=True))

            # create string
            stat_str = (f'-- {username.upper()} - MSGS: '
                        f'{user_data["month"]["messages"]} ({user_data["alltime"]["messages"]}) --')

            stat_str += f'\nTop 10 used emojis this month\n'
            limit = 0
            print(monthly_sorted_dict_descending)
            for i in monthly_sorted_dict_descending:
                just_name = self.re_pattern.findall(i)
                print(just_name)
                print(just_name[0])
                stat_str += just_name[0] + ' - ' + str(monthly_sorted_dict_descending[i]) + '\n'
                limit += 1
                if limit == 10:
                    break

            stat_str += f'\nTop 10 used emojis of all time\n'
            limit = 0
            for i in alltime_sorted_dict_descending:
                just_name = self.re_pattern.findall(i)
                stat_str += just_name[0] + ' - ' + str(alltime_sorted_dict_descending[i]) + '\n'
                limit += 1
                if limit == 10:
                    break

            await message.channel.send(f'```yaml\n\n{stat_str}```')

        except FileNotFoundError:
            await message.channel.send(f'```yaml\n\nNo data found for user id {user_id}```')

        except KeyError as e:
            log(f'[Stats] - KeyError: {e}')
            await message.channel.send(f'```yaml\n\nError loading userdata for {user_id}```')
