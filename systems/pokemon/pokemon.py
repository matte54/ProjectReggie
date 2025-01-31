import random
import json
import os
import discord

from systems.logger import debug_on, log
from systems.varmanager import VarManager

from systems.pokemon.set_data import x as set_data
from systems.pokemon.rarity_data import x as rarity_data
from systems.pokemon import pokehandler


class CardError(Exception):
    pass


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
        # Load all cards into a list
        card_dicts = []
        for file in os.listdir(f'{self.set_path}{self.working_set}'):
            if file.endswith(".json"):
                file_path = os.path.join(f'{self.set_path}{self.working_set}', file)
                with open(file_path, 'r') as json_file:
                    data = json.load(json_file)
                    card_dicts.append(data)

        # Separate trainer cards and other cards
        trainer_cards = [card for card in card_dicts if "Trainer" in card["supertype"]]
        other_cards = [card for card in card_dicts if
                       "Trainer" not in card["supertype"] and "Energy" not in card["supertype"]]

        # Create a rarity map for non-trainer cards
        rarity_map = {rarity: [] for rarity, _, _ in self.raritydata}
        for card in other_cards:
            rarity_map[card["rarity"]].append(card)

        # Flatten weights and limits from raritydata
        rarities, chances, limits = zip(*self.raritydata)

        # Initialize counters for each rarity
        rarity_counts = {rarity: 0 for rarity in rarities}

        # Initialize selection with the possibility of adding trainer cards
        self.selected_cards = []
        trainer_card_used = False  # Track if a trainer card has been added

        # Pick items respecting limits
        for _ in range(10):
            # Decide whether to add a trainer card (low probability)
            if trainer_cards and random.random() < 0.05:  # chance to pick a trainer card
                log(f'[Pokemon][DEBUG] - Adding a trainer card')
                trainer_card = random.choice(trainer_cards)
                self.selected_cards.append(trainer_card)
                # make sure only one trainer card is picked
                break

            # Filter rarities with available cards and limits not exceeded
            available_rarities = [
                (rarity, chance) for rarity, chance, limit in zip(rarities, chances, limits)
                if rarity_map[rarity] and rarity_counts[rarity] < limit
            ]

            if not available_rarities:
                # Attempt to add a trainer card as a fallback
                if trainer_cards and not trainer_card_used and random.random() < 0.1:  # 10% chance
                    log(f'[Pokemon][DEBUG] - Adding a fallback trainer card')
                    trainer_card = random.choice(trainer_cards)
                    self.selected_cards.append(trainer_card)
                    trainer_card_used = True  # Mark the trainer card as used
                    continue

            if not available_rarities:  # Break if no valid rarities are left
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

        # Fallback to fill the remaining slots, allowing duplicates
        all_cards = other_cards + trainer_cards  # Combine all cards into a single pool
        while len(self.selected_cards) < 10:
            if not all_cards:  # If there are no cards left at all
                log(f'[Pokemon] - Error, out of valid cards')
                break

            # Pick a random card from all available cards (duplicates allowed)
            item = random.choice(all_cards)
            self.selected_cards.append(item)

        if debug_on():
            log(f'[Pokemon][DEBUG] - {len(self.selected_cards)} cards picked')

        if len(self.selected_cards) < 10:
            raise CardError(f'Not enough cards selected {len(self.selected_cards)}')

        for card in self.selected_cards:
            self.card_list.append((card["id"], card["rarity"], card["name"]))
            if debug_on():
                log(f'[Pokemon][DEBUG] - {card["name"]}({card["id"]}) - {card["rarity"]}')

        # rarity sorting test
        rarity_dict = {item[0].lower(): item[1] for item in self.raritydata}
        self.card_list.sort(key=lambda card: rarity_dict.get(card[1].lower(), 1.0))

        pokecard_img_list = []
        for poke_id in self.card_list:
            try:
                # Use the sorted list to append files (using poke_id[0] for card ID)
                image_path = f'{self.images_path}{self.working_set}/images/{poke_id[0]}.png'  # poke_id[0] is the card ID
                pokecard_img_list.append(
                    discord.File(image_path, spoiler=True))
            except FileNotFoundError:
                # If the image is not found, use a default image
                log(f'[Pokemon] - Error, {self.images_path}{self.working_set}/images/{poke_id[0]}.png not found!')
                pokecard_img_list.append(
                    discord.File(f'./data/pokemon/default_card.png', spoiler=True))

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

        # Debugging to understand probabilities
        total_weight = sum(weights)
        probabilities = [w / total_weight for w in weights]
        picked_index = set_ids.index(picked_set)
        picked_probability = probabilities[picked_index]
        picked_odds_percentage = picked_probability * 100
        log(f'[Pokemon] - ID: {picked_set} odds: {picked_probability:.2%}')

        return picked_set, picked_odds_percentage
