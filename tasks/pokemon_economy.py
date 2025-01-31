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

        self.setdatalist_default = set_data

        # load setdata pkl file if exists
        if os.path.exists('./local/pokemon/setdata.pkl'):
            with open('./local/pokemon/setdata.pkl', 'rb') as file:
                self.setdatalist = pickle.load(file)
        else:
            self.setdatalist = set_data

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

                # Check if the third element is a number and if it is greater than the default value
                if isinstance(sub_modified[2], (int, float)):  # Check if the third element is numeric
                    # Ensure the value is never less than the default
                    pricedrop = random.randint(5, 30)
                    new_value = max(sub_modified[2] - pricedrop, sub_default[2])
                    # Modify the list in-place, but keep it as a list
                    self.setdatalist[i] = [sub_modified[0], sub_modified[1], new_value]
                    log(f'[Pokemon][Economy]- Incremental (${pricedrop}) price decrease of set: {self.setdatalist[i][0]}')

        await self.save_setdata()

    async def main(self):

        await asyncio.sleep(10)
        log(f'[Pokemon]- Initilizing pokémon economy')
        while self.run:

            await self.change_check()

            await asyncio.sleep(3600)
