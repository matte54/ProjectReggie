import json
import datetime

from systems.logger import log


class Tacklebox:
    def __init__(self):
        self.user_data = None
        self.shop_dict = None

    async def process_message(self, message):
        self.user_data = None
        self.shop_dict = None
        self.load_shop()
        msg = message.content.replace("$tacklebox ", "")
        if msg.startswith("shop"):
            await self.shop(message)
            return
        user_data_loaded = self.load_userdata(str(message.author.id))
        if not user_data_loaded:
            await message.channel.send(f'```yaml\n\nMissing fishing profile for user {message.author}```')
            return

        if msg.startswith("rent"):
            await self.rent(msg.replace("rent ", ""), message)
        elif msg.startswith("list"):
            await self.list_gear(message)
        else:
            await message.channel.send(f'```yaml\n\nInvalid command only accepts: RENT|LIST|SHOP```')

    async def rent(self, item, message):
        # rent x item
        if item not in self.shop_dict:
            # make sure item exists
            await message.channel.send(f'```yaml\n\nNo item by that name, try SHOP to see whats available```')
            return
        if not self.shop_dict[item][2]:
            # make sure item is available
            await message.channel.send(f'```yaml\n\nThat item is currently unavailable```')
            return
        if not self.user_data["money"] >= self.shop_dict[item][1]:
            # make sure user has the money needed
            await message.channel.send(f'```yaml\n\nYou can not afford to rent that item```')
            return
        # we passed all checks aquire the item
        log(f'[Tacklebox] - {message.author} rents {item} for {self.shop_dict[item][1]} bells')
        now = datetime.datetime.now()
        current_gear = self.user_data["gear"]
        current_gear.append((item, str(now.isoformat())))
        # update userprofile
        self.user_data["gear"] = current_gear
        self.user_data["money"] -= self.shop_dict[item][1]
        self.write_json(f"./local/fishing/profiles/{str(message.author.id)}.json", self.user_data)
        # update shop
        self.shop_dict[item][2] = False
        self.write_json("./data/fishing/items.json", self.shop_dict)
        await message.channel.send(f'```yaml\n\n{message.author} rents {item} for {self.shop_dict[item][1]} bells```')

    async def list_gear(self, message):
        # list users current items
        log(f'[Tacklebox] - {message.author} lists their items')
        if self.user_data["gear"]:
            current_time = datetime.datetime.now()
            list_string = ""
            for i in self.user_data["gear"]:
                time_difference = current_time - datetime.datetime.fromisoformat(i[1])
                time_left = datetime.timedelta(hours=3) - time_difference
                list_string += f'{i[0]} - time remaining: {str(time_left).split(".")[0]}\n'
        else:
            list_string = f'no items currently in use'
        await message.channel.send(f'```yaml\n\n{list_string}```')

    async def shop(self, message):
        # show whats available
        log(f'[Tacklebox] - {message.author} browses the shop')
        shop_string = f'**** Fishing items for rent ****\n'
        shop_string += "rent any of these unique items for 3 hours\n"
        for key, value in self.shop_dict.items():
            if value[2]:
                shop_string += f'{key} - {value[0]} - {value[1]} bells\n'
        await message.channel.send(f'```yaml\n\n{shop_string}```')

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

    def write_json(self, filepath, data):
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
