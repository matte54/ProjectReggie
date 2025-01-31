import json
import asyncio
import os
import pickle
import random


from systems.logger import log
from systems.varmanager import VarManager

from systems.pokemon.set_data import x as set_data


class Pokemoneconomy:
    def __init__(self, client):
        self.client = client
        self.varmanager = VarManager()
        self.run = True
        self.done_sale = False
        self.done_hike = False
        self.iteration = 0

        self.setdatalist_default = set_data
        self.pokemon_channels = None

        # load setdata pkl file if exists
        if os.path.exists('./local/pokemon/setdata.pkl'):
            with open('./local/pokemon/setdata.pkl', 'rb') as file:
                self.setdatalist = pickle.load(file)
        else:
            self.setdatalist = set_data

    async def collect_channel_ids(self):
        if self.varmanager.read("pokemon_channels"):
            self.pokemon_channels = self.varmanager.read("pokemon_channels")

    async def send_to_all(self, msg):
        # send to this function to post to all pokemon channels
        messages = []
        for channel in self.pokemon_channels:
            ch = self.client.get_channel(channel)
            x = await ch.send(msg)
            messages.append(x)
        return messages

    async def save_setdata(self):
        with open('./local/pokemon/setdata.pkl', 'wb') as file:
            pickle.dump(self.setdatalist, file)
        log(f'[Pokemon] - saved setdata.pkl')

    async def change_check(self):
        if os.path.exists('./local/pokemon/setdata.pkl'):
            with open('./local/pokemon/setdata.pkl', 'rb') as file:
                self.setdatalist = pickle.load(file)

        differences = []
        for i, (sub_default, sub_modified) in enumerate(zip(self.setdatalist_default, self.setdatalist)):
            if sub_default != sub_modified:
                differences.append((i, sub_default, sub_modified))

                # Check if the third element is a number
                if isinstance(sub_modified[2], (int, float)):
                    pricedrop = random.randint(5, 30)  # Random adjustment amount

                    if sub_modified[2] > sub_default[2]:  # If value is above default, decrease it
                        new_value = max(sub_modified[2] - pricedrop, sub_default[2])
                        log(f'[Pokemon][Economy]- Incremental (${pricedrop}) price decrease of set: {sub_modified[0]}')

                    elif sub_modified[2] < sub_default[2]:  # If value is below default, increase it
                        new_value = min(sub_modified[2] + pricedrop, sub_default[2])
                        log(f'[Pokemon][Economy]- Incremental (${pricedrop}) price increase of set: {sub_modified[0]}')

                    else:
                        new_value = sub_modified[2]  # No change needed

                    # Update the list in place
                    self.setdatalist[i] = [sub_modified[0], sub_modified[1], new_value]

        await self.save_setdata()

    async def set_sale(self):
        highvalue_sets = [item for item in self.setdatalist if item[2] >= 100]
        sale_set_data = random.choice(highvalue_sets)

        setid = sale_set_data[0]
        setprice = sale_set_data[2]
        sale_percent = random.randint(40, 85)

        sale = (sale_percent / 100) * setprice

        sale_set_data[2] = (int(setprice - sale))

        with open(f'./data/pokemon/setdata/{setid}_setdata.json', 'r') as json_file:
            setdata = json.load(json_file)

        await self.save_setdata()

        await self.send_to_all(f'```yaml\n\nThere is a {sale_percent}% SALE on {setid} , get a {setdata["name"]} boosterpack for ${sale_set_data[2]}\n```')

    async def set_hike(self):
        highvalue_sets = [item for item in self.setdatalist if item[2] >= 100]
        hike_set_data = random.choice(highvalue_sets)

        setid = hike_set_data[0]
        setprice = hike_set_data[2]
        hike_percent = random.randint(40, 85)

        hike = (hike_percent / 100) * setprice

        hike_set_data[2] = (int(setprice + hike))

        with open(f'./data/pokemon/setdata/{setid}_setdata.json', 'r') as json_file:
            setdata = json.load(json_file)

        await self.save_setdata()

        await self.send_to_all(
            f'```yaml\n\nThe store sets a {hike_percent}% MARKUP on {setid}, {setdata["name"]} boosterpack now costs ${hike_set_data[2]}\n```')

    async def main(self):
        await self.collect_channel_ids()

        await asyncio.sleep(10)
        log(f'[Pokemon]- Initilizing pokémon economy')
        while self.run:

            self.iteration += 1  # Increase iteration count
            sale_chance = min(5 + self.iteration * 2, 100)
            hike_chance = min(5 + self.iteration * 2, 100)

            if not self.done_sale and random.randint(1, 100) < sale_chance:
                await self.set_sale()
                self.done_sale = True

            if not self.done_hike and random.randint(1, 100) < hike_chance:
                await self.set_hike()
                self.done_hike = True

            await asyncio.sleep(3600)
            await self.change_check()
