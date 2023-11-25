import json
import os
import re
from systems.logger import log
from systems.varmanager import VarManager


class Guildstats:
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
        guild_id = str(message.guild.id)
        guild_name = str(message.guild.name)
        log(f'[Stats] - {message.author} is listing {guild_name}´s stats')
        try:
            with open(f'./local/statistics/guild/{guild_id}.json', "r") as f:
                guild_data = json.load(f)

            # sort monthly emojis
            m_emojis_dict = guild_data["month"]["emojis"]
            emoji_monthly_sorted_dict_descending = dict(sorted(m_emojis_dict.items(), key=lambda x: x[1], reverse=True))

            # sort alltime emojis
            a_emojis_dict = guild_data["alltime"]["emojis"]
            emoji_alltime_sorted_dict_descending = dict(sorted(a_emojis_dict.items(), key=lambda x: x[1], reverse=True))

            # sort monthly users
            m_users_dict = guild_data["month"]["users"]
            user_monthly_sorted_dict_descending = dict(sorted(m_users_dict.items(), key=lambda x: x[1], reverse=True))

            # sort alltime users
            a_users_dict = guild_data["alltime"]["users"]
            user_alltime_sorted_dict_descending = dict(sorted(a_users_dict.items(), key=lambda x: x[1], reverse=True))

            # create string
            stat_str = (f'-- {guild_name.upper()} - MSGS: '
                        f'{guild_data["month"]["messages"]} ({guild_data["alltime"]["messages"]}) --')

            stat_str += f'\nTop 5 most active users this month\n'
            limit = 0
            for i in user_monthly_sorted_dict_descending:
                username_str = self.get_user_name(i)
                stat_str += username_str + ' - ' + str(user_monthly_sorted_dict_descending[i]) + '\n'
                limit += 1
                if limit == 5:
                    break

            stat_str += f'\nTop 5 most active users of all time\n'
            limit = 0
            for i in user_alltime_sorted_dict_descending:
                username_str = self.get_user_name(i)
                stat_str += username_str + ' - ' + str(user_alltime_sorted_dict_descending[i]) + '\n'
                limit += 1
                if limit == 5:
                    break

            # add emoji lists keep it to 5 here or will be a long message
            stat_str += f'\nTop 5 used emojis this month\n'
            limit = 0
            for i in emoji_monthly_sorted_dict_descending:
                just_name = self.re_pattern.findall(i)
                stat_str += just_name[0] + ' - ' + str(emoji_monthly_sorted_dict_descending[i]) + '\n'
                limit += 1
                if limit == 5:
                    break

            stat_str += f'\nTop 5 used emojis of all time\n'
            limit = 0
            for i in emoji_alltime_sorted_dict_descending:
                just_name = self.re_pattern.findall(i)
                stat_str += just_name[0] + ' - ' + str(emoji_alltime_sorted_dict_descending[i]) + '\n'
                limit += 1
                if limit == 5:
                    break

            await message.channel.send(f'```yaml\n\n{stat_str}```')

        except FileNotFoundError:
            await message.channel.send(f'```yaml\n\nNo data found for guild id {guild_id}```')

        except KeyError as e:
            log(f'[Stats] - KeyError: {e}')
            await message.channel.send(f'```yaml\n\nError loading data for {guild_id}```')