import random
import json
import os
import discord

from systems.logger import debug_on, log
from systems.varmanager import VarManager

from systems.pokemon.set_data import x as set_data
from systems.pokemon.rarity_data import x as rarity_data
from systems.pokemon import pokehandler


class PokemonTCG:
    def __init__(self, client):
        self.client = client
        self.pokehandler = pokehandler.Pokehandler(self.client)
        self.setdata = set_data  # all the set data (tuples)
        self.setnames = [item[0] for item in self.setdata]  # only the ids (list)
        self.set_path = "./data/pokemon/sets/"
        self.images_path = "./data/pokemon/images/"
        self.working_set = ""

        self.raritydata = rarity_data  # card rarities (tuples)
        self.card_total = 0
        self.card_list = []
        self.selected_cards = []

    async def process_input(self, query):
        # entry point query should be random or a setid
        # else returns
        # reset
        self.working_set = ""
        self.card_total = 0
        self.card_list = []
        self.selected_cards = []

        if query == "random":
            self.working_set = self.pick_random_set()
        if query not in self.setnames and query != "random":
            if debug_on():
                log(f'[Pokemon] - No set found by that name')
            return False, False
        else:
            self.working_set = query
            if debug_on():
                log(f'[Pokemon] - Using set id: {self.working_set}')

            return await self.pick_cards()

    async def pick_cards(self):
        # load all cards into list
        card_dicts = []
        for file in os.listdir(f'{self.set_path}{self.working_set}'):
            if file.endswith(".json"):
                file_path = os.path.join(f'{self.set_path}{self.working_set}', file)
                with open(file_path, 'r') as json_file:
                    data = json.load(json_file)
                    card_dicts.append(data)

        # remove trainer and energy cards
        for i in range(len(card_dicts) - 1, -1, -1):
            if "Trainer" in card_dicts[i]["supertype"] or "Energy" in card_dicts[i]["supertype"]:
                del card_dicts[i]

        # Create a rarity map
        rarity_map = {rarity: [] for rarity, _, _ in self.raritydata}
        for d in card_dicts:
            rarity_map[d["rarity"]].append(d)

        # Flatten weights and limits from raritydata
        rarities, chances, limits = zip(*self.raritydata)

        # Initialize counters for each rarity
        rarity_counts = {rarity: 0 for rarity in rarities}

        # Pick items respecting limits
        self.selected_cards = []
        for _ in range(10):
            # Filter rarities with available cards and limits not exceeded
            available_rarities = [
                (rarity, chance) for rarity, chance, limit in zip(rarities, chances, limits)
                if rarity_map[rarity] and rarity_counts[rarity] < limit
            ]
            if not available_rarities:  # Stop if no valid rarities are left
                break

            rarities, chances = zip(*available_rarities)

            # Pick a rarity based on weight
            chosen_rarity = random.choices(rarities, weights=chances, k=1)[0]
            # Select a random item from the chosen rarity group
            item = random.choice(rarity_map[chosen_rarity])
            self.selected_cards.append(item)
            # Remove the item to avoid duplicates
            rarity_map[chosen_rarity].remove(item)
            # Increment the counter for the chosen rarity
            rarity_counts[chosen_rarity] += 1

        # Fallback to fill the remaining slots
        while len(self.selected_cards) < 10:
            # Filter rarities with available cards (ignore limits here)
            available_rarities = [
                rarity for rarity in rarities if rarity_map[rarity]
            ]
            if not available_rarities:  # Break if no cards are left
                break

            # Prioritize rarer cards by reversing the original order
            chosen_rarity = available_rarities[-1]
            # Select a random item from the chosen rarity group
            item = random.choice(rarity_map[chosen_rarity])
            self.selected_cards.append(item)
            # Remove the item to avoid duplicates
            rarity_map[chosen_rarity].remove(item)

        if debug_on():
            log(f'[Pokemon] - {len(self.selected_cards)} cards picked')

        for card in self.selected_cards:
            self.card_list.append((card["id"], card["rarity"], card["name"]))

        # add into discord gallery upload
        pokecard_img_list = []
        for poke_id in self.card_list:
            pokecard_img_list.append(discord.File(f'{self.images_path}{self.working_set}/images/{poke_id[0]}.png', spoiler=True))

        return self.selected_cards, pokecard_img_list

    async def pick_random_set(self):
        # --- Picks random set from set_data.py file according to chances ---
        set_ids = []
        for items in self.setdata:
            set_ids.append(items[0])
        weights = []
        for items in self.setdata:
            weights.append(items[1])

        picked_set = random.choices(set_ids, weights=weights, k=1)[0]

        if debug_on():
            # --- Just some debugging to help tweak chance numbers ---
            total_weight = sum(weights)
            probabilities = [w / total_weight for w in weights]
            picked_probability = probabilities[set_ids.index(picked_set)]
            picked_index = set_ids.index(picked_set)

            log(f'[Pokemon] - ID: {picked_set} rarity: {weights[picked_index]:%} odds: {picked_probability:%}')

        return picked_set
