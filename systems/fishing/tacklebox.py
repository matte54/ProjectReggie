import json
import os
import re

from systems.logger import log

class Tacklebox:
    def __init__(self):
        self.user_data = None
        self.shop_dict = None
        self.load_shop()


    async def process_message(self, message):
        msg = message.content.replace("$tacklebox ", "")
        if msg.startswith("shop"):
            self.shop(message.author)
        user_data_loaded = self.load_userdata(str(message.author.id))
        if not user_data_loaded:
            await message.channel.send(f'```yaml\n\nMissing fishing profile for user {message.author}```')
            return

        if msg.startswith("buy"):
            self.buy(msg.replace("buy ", ""))
        elif msg.startswith("list"):
            self.list(message.author)
        else:
            await message.channel.send(f'```yaml\n\nInvalid command only accepts: BUY|LIST|SHOP```')


    def buy(self, item):
        # buy x item
        print("buying")

    def list(self, member_obj):
        # list users current items
        print("listing")

    def shop(self, member_obj):
        # show whats available, DM
        print("shopping")

    def load_shop(self):
        with open("./data/fishing/items.json", "r") as f:
            self.shop_dict = json.load(f)

    def load_userdata(self, user_id_str):
        self.user_data = None
        try:
            with open(f"./local/fishing/profiles/{user_id_str}.json", "r") as f:
                self.user_data = json.load(f)
            return True
        except FileNotFoundError:
            return False

