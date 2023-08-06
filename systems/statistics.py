import re
import os
import json
import yake

from systems.logger import debug_on, log


class Statistics:
    def __init__(self, client):
        self.client = client
        self.stats_main_path = "./local/statistics/"
        self.stats_user_path = "./local/statistics/user/"
        self.stats_guild_path = "./local/statistics/guild/"
        self.emoji_pattern = r"<:[a-zA-Z0-9]+:\d+>"

        self.message_str = None
        self.guild_id = None
        self.user_id = None
        self.username = None

        self.guild_data = None
        self.user_data = None

    def input(self, message):
        self.message_str = message.content
        self.guild_id = str(message.guild.id)
        self.user_id = str(message.author.id)
        self.username = message.author
        self.file_check(self.guild_id, self.user_id)  # make sure there are files for the input
        with open(f'{self.stats_guild_path}{self.guild_id}.json', "r") as f:
            self.guild_data = json.load(f)
        with open(f'{self.stats_user_path}{self.user_id}.json', "r") as f:
            self.user_data = json.load(f)

        self.messages_plus_one()  # add plus one to all message stats for guild and user
        self.handle_emojis()  # look for emojis and add to stats
        self.find_keywords()

        self.write_json(f'{self.stats_guild_path}{self.guild_id}.json', self.guild_data)
        self.write_json(f'{self.stats_user_path}{self.user_id}.json', self.user_data)

    def find_keywords(self):
        # straight from the yake manual, (experimental)
        language = "en"
        max_ngram_size = 2
        deduplication_threshold = 0.9
        deduplication_algo = 'seqm'
        windowSize = 1
        numOfKeywords = 5
        accepted_value = 0.008  # this needs tweaking

        custom_kw_extractor = yake.KeywordExtractor(lan=language, n=max_ngram_size, dedupLim=deduplication_threshold,
                                                    dedupFunc=deduplication_algo, windowsSize=windowSize,
                                                    top=numOfKeywords, features=None)
        keywords = custom_kw_extractor.extract_keywords(self.message_str)

        decent_keywords = []
        for kw in keywords:
            if kw[1] < accepted_value:
                decent_keywords.append(kw)
        if not decent_keywords:
            return None
        sorted_data = sorted(decent_keywords, key=lambda x: x[1])
        chosen_keyword = sorted_data[0][0]
        if debug_on():
            log(f'[Statistics] - added keyword "{chosen_keyword}" for user {self.username}')
        # add keyword to users statistics
        if chosen_keyword in self.user_data["alltime"]["keywords"]:
            self.user_data["alltime"]["keywords"][chosen_keyword] += 1
        else:
            self.user_data["alltime"]["keywords"][chosen_keyword] = 1

    def messages_plus_one(self):
        # add nr of messages to guild and user stats
        self.guild_data["alltime"]["messages"] += 1
        self.guild_data["month"]["messages"] += 1

        self.user_data["alltime"]["messages"] += 1
        self.user_data["month"]["messages"] += 1

    def handle_emojis(self):
        emoji_list = re.findall(self.emoji_pattern, self.message_str)
        if not emoji_list:
            return  # when there is no emojis detected just staph
        for emoji in emoji_list:
            # add emoji to guild statistics
            if emoji in self.guild_data["alltime"]["emojis"]:
                self.guild_data["alltime"]["emojis"][emoji] += 1
            else:
                self.guild_data["alltime"]["emojis"][emoji] = 1

            if emoji in self.guild_data["month"]["emojis"]:
                self.guild_data["month"]["emojis"][emoji] += 1
            else:
                self.guild_data["month"]["emojis"][emoji] = 1

            # add emoji to users statistics
            if emoji in self.user_data["alltime"]["emojis"]:
                self.user_data["alltime"]["emojis"][emoji] += 1
            else:
                self.user_data["alltime"]["emojis"][emoji] = 1

            if emoji in self.user_data["month"]["emojis"]:
                self.user_data["month"]["emojis"][emoji] += 1
            else:
                self.user_data["month"]["emojis"][emoji] = 1

    def file_check(self, guild_id, user_id):
        if not os.path.isfile(f'{self.stats_guild_path}{guild_id}.json'):
            blank_dict = {"alltime": {
                "messages": 0,
                "emojis": {}},
                "month": {
                    "messages": 0,
                    "emojis": {}
                }}
            self.write_json(f'{self.stats_guild_path}{guild_id}.json', blank_dict)
        if not os.path.isfile(f'{self.stats_user_path}{user_id}.json'):
            blank_dict = {"alltime": {
                "messages": 0,
                "emojis": {},
                "keywords": {}},
                "month": {
                    "messages": 0,
                    "emojis": {}
                }}
            self.write_json(f'{self.stats_user_path}{user_id}.json', blank_dict)

    def write_json(self, filepath, data):
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
