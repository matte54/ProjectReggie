# handler that reads the emojis.json, checks if woodhouse can use it in the server

import json
import random
import os


class Emojihandler:
    def __init__(self, client):
        self.client = client
        self.emojipool = []

    # this function needs the channelid of where its going to be used
    def emojihandler(self, channelid):
        # get guild id from channelid
        channel = self.client.get_channel(channelid)
        guildid = channel.guild.id

        with open("./local/emojis.json", "r") as f:
            data = json.load(f)

        # add upp to 3 popular emojis from the guild stats (if found) to the pool
        list_of_popular_emojis = self.check_stats(guildid)
        if list_of_popular_emojis:
            for i in list_of_popular_emojis:
                self.emojipool.append(i)
        # add 3 random default emojis to pool
        for i in random.choices(data["default"], k=3):
            self.emojipool.append(i)
        # add 3 guild specific emojis to pool
        for i in random.choices(data[str(guildid)], k=3):
            self.emojipool.append(i)
        print(self.emojipool)
        return random.choice(self.emojipool) # return a random choice from the pool

    def check_stats(self, guildid):
        # this checks the guilds popular emojis
        if os.path.isfile(f'./local/statistics/guild/{guildid}.json'):
            with open(f'./local/statistics/guild/{guildid}.json', "r") as f:
                guild_emoji_stats = json.load(f)
            if len(guild_emoji_stats) > 0:
                sorted_dict = sorted(guild_emoji_stats["alltime"]["emojis"], reverse=True)
                if len(sorted_dict) < 3:
                    return sorted_dict
                else:
                    return sorted_dict[0:3]
        return None

