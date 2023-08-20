# a way to query a fish to give back some data of it
import os
import json
import discord

from systems.logger import log

class Fishbase:
    def __init__(self):
        self.wr_file = "./local/fishing/wr.json"
        self.buckets_path = "./local/fishing/buckets/"
        self.fishdatabases_path = "./data/fishing/databases/"
        self.databases_list = ["class1.json", "class2.json", "class3.json", "class4.json",
                               "class5.json", "class6.json", "class7.json"]
        self.id_file = "./data/etc/ids.json"
        self.embed = None
        self.query = None
        self.fish = None
        self.fish_wr = None
        self.wr_time = None
        self.wr_holder = None
        self.fish_class = None
        self.bucket_fish = []

    async def command(self, message):
        self.query = message.content.replace("$fishbase ", "").capitalize()
        log(f'[Fishbase] - {message.author} quries {self.query}')
        self.fish = self.find_fish_data()
        if not self.fish:
            await message.channel.send(f'```yaml\n\nThere is no fish by that name in the database```')
            return
        self.find_wr()
        self.search_buckets()
        self.create_embed()

        await message.channel.send(embed=self.embed)

    def find_fish_data(self):
        self.fish = None
        self.fish_class = None
        for file in self.databases_list:
            with open(f'{self.fishdatabases_path}{file}', "r") as f:
                class_data = json.load(f)
            if self.query in class_data:
                self.fish = class_data[self.query]
                self.fish_class = file[5:].replace(".json", "")
                break
        return self.fish

    def search_buckets(self):
        self.bucket_fish = []
        bucket_list = os.listdir(self.buckets_path)
        if bucket_list:
            for bucket in bucket_list:
                with open(f'{self.buckets_path}{bucket}', "r") as f:
                    bucket_data = json.load(f)
                if self.query in bucket_data:
                    id_str = bucket.replace(".json", "")
                    with open(f'{self.id_file}', "r") as f:
                        id_data = json.load(f)
                    username = id_data[id_str]
                    fish_tuple = (username, bucket_data[self.query]["weight"])
                    self.bucket_fish.append(fish_tuple)

    def find_wr(self):
        self.fish_wr = None
        self.wr_holder = None
        self.wr_time = None
        with open(f'{self.wr_file}', "r") as f:
            wr_data = json.load(f)
        if self.query in wr_data:
            self.fish_wr = wr_data[self.query]["weight"]
            self.wr_holder = wr_data[self.query]["holder"]
            self.wr_time = wr_data[self.query]["time"][:10]


    def create_embed(self):
        self.embed = None
        self.embed = discord.Embed(title=f'{self.query}', description=f'{self.fish["fact"]}')
        self.embed.set_author(name="Fish Encylopedia")
        self.embed.add_field(name=f'Class {self.fish_class}',
                             value=f'Average size\n{self.fish["min_weight"] + self.fish["max_weight"] / 2} lbs')
        if self.fish_wr:
            self.embed.add_field(name="World Record", value=f'{self.fish_wr} lbs\nby {self.wr_holder}\n{self.wr_time}',
                                 inline=True)
        else:
            self.embed.add_field(name="", value=f'', inline=True)
        self.embed.add_field(name="Rarity", value=f'{self.fish["rarity"] * 100}%', inline=True) # this isent quite right but will do for now
        if self.fish["unique"]:
            self.embed.add_field(name="Unique", value="Yes", inline=True)
        else:
            self.embed.add_field(name="Unique", value="No", inline=True)
        if self.bucket_fish:
            holder_list = ""
            for i in self.bucket_fish:
                holder_list += f'{i[0]} {i[1]} lbs\n'
            self.embed.add_field(name="Holders", value=f'{holder_list}')
        else:
            self.embed.add_field(name="Holders", value=f"None")
        self.embed.set_thumbnail(url=f'http://thedarkzone.se:8080/fishicons/{self.query.capitalize().replace(" ", "")}.png')