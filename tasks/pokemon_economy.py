import json
import asyncio
import os
import pickle
import random
import discord
import math


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

        self.balance_set_pricing()

        # load setdata pkl file if exists
        if os.path.exists('./local/pokemon/setdata.pkl'):
            with open('./local/pokemon/setdata.pkl', 'rb') as file:
                self.setdatalist = pickle.load(file)
        else:
            self.setdatalist = self.setdatalist_default

    async def collect_channel_ids(self):
        if self.varmanager.read("pokemon_channels"):
            self.pokemon_channels = self.varmanager.read("pokemon_channels")

    def balance_set_pricing(self):
        # set inflation of set prices depending on money in circulation
        total = 0
        directory = './local/pokemon/profiles/'
        number_of_players = 0
        for filename in os.listdir(directory):
            if filename.endswith(".json"):
                filepath = os.path.join(directory, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                        if "profile" in data and "money" in data["profile"] and isinstance(data["profile"]["money"],
                                                                                           (int, float)):
                            total += data["profile"]["money"]
                            number_of_players += 1
                    except json.JSONDecodeError:
                        print(f"Error decoding {filename}, skipping...")

        money_in_circulation = int(total)
        base_money = 1000

        if number_of_players == 0:
            return
        for item in self.setdatalist_default:
            base_price = item[2]
            new_money_per_player = money_in_circulation / number_of_players
            new_price = base_price * math.sqrt(new_money_per_player / base_money)
            item[2] = int(new_price)
            #print(f'{item[0]} BASE: {base_price}, INFLATED: {item[2]}')

    async def send_to_all(self, msg):
        max_retries = 3
        delay = 2
        messages = []

        for channel_id in self.pokemon_channels:
            for attempt in range(max_retries):
                ch = self.client.get_channel(channel_id)

                if ch is None:
                    log(f'[Pokemon]- Channel {channel_id} not found. Retrying in {delay * (2 ** attempt)}s...')
                else:
                    try:
                        x = await ch.send(msg)
                        messages.append(x)
                        break  # Successfully sent, exit retry loop
                    except (discord.HTTPException, discord.Forbidden, discord.NotFound) as e:
                        log(f'[Pokemon]- Error sending message (attempt {attempt + 1}/{max_retries}): {e}')

                await asyncio.sleep(delay * (2 ** attempt))

            else:  # This else runs only if all retries fail
                log(f'[Pokemon]- Failed to send message to {channel_id} after {max_retries} retries.')

        return messages

    async def save_setdata(self):
        with open('./local/pokemon/setdata.pkl', 'wb') as file:
            pickle.dump(self.setdatalist, file)
        log(f'[Pokemon] - saved setdata.pkl')

    def write_json(self, filepath, data):
        with open(filepath, "w", encoding="UTF-8") as f:
            json.dump(data, f, indent=4)

    async def change_check(self):
        if os.path.exists('./local/pokemon/setdata.pkl'):
            with open('./local/pokemon/setdata.pkl', 'rb') as file:
                self.setdatalist = pickle.load(file)

        changeslist = []
        differences = []
        for i, (sub_default, sub_modified) in enumerate(zip(self.setdatalist_default, self.setdatalist)):
            if sub_default != sub_modified:
                differences.append((i, sub_default, sub_modified))

                # Check if the third element is a number
                if isinstance(sub_modified[2], (int, float)):
                    pricedrop = random.randint(1, 3)  # Random adjustment amount

                    if sub_modified[2] > sub_default[2]:  # If value is above default, decrease it
                        new_value = max(sub_modified[2] - pricedrop, sub_default[2])
                        changeslist.append(f'{sub_modified[0]}: -{pricedrop}')

                    elif sub_modified[2] < sub_default[2]:  # If value is below default, increase it
                        new_value = min(sub_modified[2] + pricedrop, sub_default[2])
                        changeslist.append(f'{sub_modified[0]}: +{pricedrop}')

                    else:
                        new_value = sub_modified[2]  # No change needed

                    # Update the list in place
                    self.setdatalist[i] = [sub_modified[0], sub_modified[1], new_value]

        if changeslist:
            await self.save_setdata()
            log(f'[Pokemon][Economy] - adjusted setprices: {changeslist}')

    async def set_sale(self):
        await self.collect_channel_ids()

        with open(f'./local/pokemon/purchase_records.json', 'r') as json_file:
            records_data = json.load(json_file)

        # Consider every set in self.setdatalist as 0 if it's not in records_data
        all_sets_with_purchases = {item[0]: records_data.get(item[0], 0) for item in self.setdatalist}

        # Find the lowest purchase count
        min_purchases = min(all_sets_with_purchases.values(), default=0)

        # Get all sets that match this lowest purchase count
        low_purchase_sets = [item for item in self.setdatalist if all_sets_with_purchases[item[0]] == min_purchases]

        # Use weighted random choice, favoring lower purchase counts (inverted weights)
        weights = [1 / (all_sets_with_purchases[item[0]] + 1) for item in
                   low_purchase_sets]  # +1 to avoid division by zero

        sale_set_data = random.choices(low_purchase_sets, weights=weights, k=1)[0]

        setid = sale_set_data[0]
        setprice = sale_set_data[2]
        sale_percent = random.randint(40, 85)

        sale = (sale_percent / 100) * setprice
        sale_set_data[2] = int(setprice - sale)

        with open(f'./data/pokemon/setdata/{setid}_setdata.json', 'r') as json_file:
            setdata = json.load(json_file)

        await self.save_setdata()

        await self.send_to_all(f'```yaml\n\nThere is a {sale_percent}% SALE on {setid} , get a {setdata["name"]} boosterpack for ${sale_set_data[2]}\n```')

    async def set_hike(self):
        await self.collect_channel_ids()

        with open(f'./local/pokemon/purchase_records.json', 'r') as json_file:
            records_data = json.load(json_file)

        if not records_data:
            log(f'[Pokemon][Economy] - No sets for markup found')
            return

        # Map all sets in self.setdatalist with their recorded purchases (default 0)
        all_sets_with_purchases = {item[0]: records_data.get(item[0], 0) for item in self.setdatalist}

        # Count how many sets have more than 0 purchases
        sets_with_purchases = [item for item in all_sets_with_purchases if all_sets_with_purchases[item] > 0]

        # If there are fewer than 5 sets with purchases, consider sets with 0 purchases
        if len(sets_with_purchases) < 5:
            eligible_sets = list(self.setdatalist)  # Include all sets, including those with 0 purchases
        else:
            eligible_sets = [item for item in self.setdatalist if all_sets_with_purchases.get(item[0], 0) > 0]

        # Assign weights based on purchase count (higher purchase = higher weight)
        weights = [2 ** all_sets_with_purchases[item[0]] if all_sets_with_purchases[item[0]] > 0 else 1 for item in
                   eligible_sets]

        # Debug output for eligible sets and weights
        log(f'[Pokemon][Economy] - Eligible Sets for markup: {[item[0] for item in eligible_sets]}')

        #for set_item, weight in zip(eligible_sets, weights):
        #    print(f"Set: {set_item[0]}, Purchases: {all_sets_with_purchases[set_item[0]]}, Weight: {weight}")

        # Pick a set using weighted random selection
        hike_set_data = list(random.choices(eligible_sets, weights=weights, k=1)[0])

        setid = hike_set_data[0]
        setprice = hike_set_data[2]
        hike_percent = random.randint(40, 85)

        hike = (hike_percent / 100) * setprice
        hike_set_data[2] = int(setprice + hike)

        with open(f'./data/pokemon/setdata/{setid}_setdata.json', 'r') as json_file:
            setdata = json.load(json_file)

        # remove 1 entry from purchase records if markuped
        if setid in records_data:
            if records_data[setid] > 0:
                records_data[setid] -= 1
        else:
            records_data[setid] = 0
        self.write_json(f'./local/pokemon/purchase_records.json', records_data)

        await self.save_setdata()
        log(f'[Pokemon][Economy] - setting {hike_percent}% MARKUP on {setid} now costs ${hike_set_data[2]}')
        await self.send_to_all(
            f'```yaml\n\nThe store sets a {hike_percent}% MARKUP on {setid}, {setdata["name"]} boosterpack now costs ${hike_set_data[2]}\n```')

    async def main(self):
        await self.collect_channel_ids()

        await asyncio.sleep(10)
        log(f'[Pokemon][Economy] - Initilizing')
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
