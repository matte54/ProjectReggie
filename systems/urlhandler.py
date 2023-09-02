# adapted from rogues original
import json
import random
import os
import yake

from systems.logger import log

class Urlhandler:
    def __init__(self, client):
        self.client = client
        self.data = None
        self.user_id = None
        self.channel = None
        self.keywords = []

    async def get_url(self, channel, user_id):
        self.user_id = None
        with open('./systems/scraper/data.json') as f:
            self.data = json.load(f)
        # Get user data if its not coming from reflex
        if user_id:
            self.user_id = user_id
            await self.get_user_keywords()
        # else get recent channel keywords
        if channel:
            self.channel = channel
            await self.get_activity_keywords()
        log(f'[Urlhandler] - Found keywords: {self.keywords}')
        url_pool = self.find_relations()

        return random.choice(url_pool)

    def find_relations(self):
        url_pool = []
        if self.keywords:
            for i in self.data.keys():
                for e in self.data[i].keys():
                    for tag in self.data[i][e]["tags"]:
                        if tag in self.keywords:
                            if self.data[i][e]["link"].startswith("https://v.redd.it"):
                                url_pool.append(self.data[i][e]["dlink"])
                            else:
                                url_pool.append(self.data[i][e]["dlink"])
        else:
            for i in self.data.keys():
                for e in self.data[i].keys():
                    link = self.data[i][e]["dlink"]
                    if link.startswith("https://v.redd.it"):
                        link = self.data[i][e]["link"]
                    url_pool.append(link)
        if not url_pool:
            for i in self.data.keys():
                for e in self.data[i].keys():
                    link = self.data[i][e]["dlink"]
                    if link.startswith("https://v.redd.it"):
                        link = self.data[i][e]["link"]
                    url_pool.append(link)

        return url_pool

    async def get_user_keywords(self):
        self.keywords = []
        templist = []
        if os.path.exists(f'./local/statistics/user/{self.user_id}.json'):
            with open(f'./local/statistics/user/{self.user_id}.json') as f:
                userdata = json.load(f)
            for key in userdata["alltime"]["keywords"]:
                keyword_tuple = (key , userdata["alltime"]["keywords"][key])
                templist.append(keyword_tuple)
            sorted_list = sorted(templist, key=lambda x: x[1], reverse=True)
            top_three = sorted_list[:3]
            for i in top_three:
                self.keywords.append(i[0])

    async def get_activity_keywords(self):
        self.keywords = []
        # yake stuff
        language = "en"
        max_ngram_size = 1
        deduplication_threshold = 0.9
        deduplication_algo = 'seqm'
        window_size = 1
        num_of_keywords = 25
        accepted_value = 0.15  # this needs tweaking
        custom_kw_extractor = yake.KeywordExtractor(lan=language, n=max_ngram_size,
                                                    dedupLim=deduplication_threshold,
                                                    dedupFunc=deduplication_algo, windowsSize=window_size,
                                                    top=num_of_keywords, features=None)
        async for message in self.channel.history(limit=5):
            if not message.author.bot:
                keywords = custom_kw_extractor.extract_keywords(message.content)
                for kw in keywords:
                    if kw[1] < accepted_value:
                        self.keywords.append(kw[0])
