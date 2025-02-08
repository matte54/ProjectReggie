import random
import json
import os
import re

from systems.logger import debug_on, log
from systems.pokemon.effectiveness_data import type_effectiveness
from systems.pokemon.halfed_atks import halfed
from systems.pokemon.threeforths_atks import threeforths
from systems.pokemon.whitelisted import whitelist

# configurable constants
NONE_DAMAGE_DEFAULT = 10

debug_on = False

class Battle:
    def __init__(self):
        self.profiles_path = "./local/pokemon/profiles/"
        self.player1_data = {}
        self.player2_data = {}
        self.battlelog = f'```yaml\n\n'
        self.log_list = []

    def get_profile(self, userid):
        if os.path.isfile(f"{self.profiles_path}{userid}.json"):
            with open(f"{self.profiles_path}{userid}.json", "r") as f:
                data = json.load(f)
        return data, f"{self.profiles_path}{userid}.json"

    def get_user_id(self, username):
        # input username get userid from database file
        if os.path.exists(f'./data/etc/ids.json'):
            with open(f'./data/etc/ids.json', "r") as f:
                id_data = json.load(f)
            match = [key for key, value in id_data.items() if value == username]
            return int(match[0])

    def write_json(self, filepath, data):
        with open(filepath, "w", encoding="UTF-8") as f:
            json.dump(data, f, indent=4)

    async def handle_battle_outcome(self, winner, loser, winner_xp, loser_xp):
        w_lvlup = None
        l_lvlup = None
        # load both profiles
        winner_userid = self.get_user_id(winner)
        winner_data, winner_path = self.get_profile(winner_userid)
        loser_userid = self.get_user_id(loser)
        loser_data, loser_path = self.get_profile(loser_userid)

        # add stats
        winner_data["profile"]["battles_won"] += 1
        loser_data["profile"]["battles_lost"] += 1

        # calculate experience gains
        base_reward = 20
        cap = 200

        gap_factor = min(winner_xp, loser_xp) / max(winner_xp, loser_xp)
        winner_reward = base_reward * (1 + gap_factor + loser_xp / winner_xp)
        loser_reward = base_reward * (1 + gap_factor * (winner_xp / loser_xp))

        # Cap the rewards
        winner_reward = int(min(winner_reward, cap))
        loser_reward = int(min(loser_reward, cap))

        log(f'[Pokemon] - Winner {winner} had hand value: {winner_xp} and is rewarded {winner_reward}')
        log(f'[Pokemon] - Loser {loser} had hand value: {loser_xp} and is rewarded {loser_reward}')

        # handle xp to profiles
        # winner
        if winner_data["profile"]["xp"] + winner_reward >= winner_data["profile"]["xp_cap"]:
            diffrence = (winner_data["profile"]["xp"] + winner_reward) - winner_data["profile"]["xp_cap"]
            winner_data["profile"]["level"] += 1
            winner_data["profile"]["xp"] = diffrence
            winner_data["profile"]["xp_cap"] += (30 + winner_data["profile"]["level"])
            w_lvlup = winner_data["profile"]["level"]
        else:
            winner_data["profile"]["xp"] += winner_reward

        # loser
        if loser_data["profile"]["xp"] + loser_reward >= loser_data["profile"]["xp_cap"]:
            diffrence = (loser_data["profile"]["xp"] + loser_reward) - loser_data["profile"]["xp_cap"]
            loser_data["profile"]["level"] += 1
            loser_data["profile"]["xp"] = diffrence
            loser_data["profile"]["xp_cap"] += (30 + loser_data["profile"]["level"])
            l_lvlup = loser_data["profile"]["level"]
        else:
            loser_data["profile"]["xp"] += loser_reward

        # prices here
        results_msg = f'```yaml\n\n'
        priceroll = bool(random.getrandbits(1))
        if priceroll:
            # money calculations with chances of high price
            price_weight = random.random() ** 2
            pricemoney = int(50 + (250 - 50) * price_weight)

            winner_data["profile"]["money"] += pricemoney
            results_msg += f'{winner} won ${pricemoney} and gained {winner_reward} xp\n'
        else:
            winner_data["profile"]["last"] = ""
            results_msg += f'{winner} won a free random boosterpack(claim it with $tcg free) and gained {winner_reward} xp\n'

        results_msg += f'{loser} gained {loser_reward} xp\n'
        if w_lvlup:
            results_msg += f'{winner} leveled up! {winner} is now level {w_lvlup}\n'
        if l_lvlup:
            results_msg += f'{loser} leveled up! {loser} is now level {l_lvlup}\n'

        results_msg += f'```'

        self.write_json(winner_path, winner_data)
        self.write_json(loser_path, loser_data)

        return results_msg

    def extract_damage_value(self, damage, default=NONE_DAMAGE_DEFAULT):
        # If damage is None or not a string, convert it to string
        if damage is None:
            damage = str(default)
        elif not isinstance(damage, str):
            damage = str(damage)

        # Handle the case for empty strings or strings that result in empty values after cleaning
        if not damage or damage.strip() == "":
            return int(default)

        # Remove all non-numeric characters and handle common symbols like '×'
        clean_damage = re.sub(r'[^0-9]', '', damage)

        # If the cleaned damage is a valid numeric string, return it as an integer
        if clean_damage.isdigit():
            return int(clean_damage)

        # If no valid digits were found, return the default value as an integer
        return int(default)

    async def calculate_effectiveness(self, base_damage, attack_type, target_type):
        type_aliases = {
            "Metal": "Steel",
            "Electric": "Lightning",
            "Darkness": "Dark",
        }

        attack_type = type_aliases.get(attack_type, attack_type)
        target_type = type_aliases.get(target_type, target_type)

        # effectiveness
        if target_type in type_effectiveness[attack_type]["super_effective"]:
            base_damage *= 2.0
            e = "it's super effective "
            return base_damage, e
        elif target_type in type_effectiveness[attack_type]["not_very_effective"]:
            base_damage *= 0.5
            e = "it's not very effective "
            return base_damage, e
        elif target_type in type_effectiveness[attack_type]["no_effect"]:
            base_damage = base_damage
            e = ""
            return base_damage, e
        elif target_type in type_effectiveness[attack_type]["resistant_to"]:
            base_damage = 0
            e = "it doesn't affect "
            return base_damage, e

        e = ""
        return base_damage, e

    async def weak_n_res(self, atkrtype, defrcard, dmg):
        # Weakness and resistance check
        if "weaknesses" in defrcard:
            for weakness in defrcard["weaknesses"]:
                if atkrtype == weakness["type"]:
                    dmg = dmg * 1.5
                    if debug_on:
                        log(f'[Pokemon][DEBUG] - {defrcard["name"]} is weak against: {atkrtype}')
                    weak = True
                    resi = False
                    return int(dmg), weak, resi
        if "resistances" in defrcard:
            for resistance in defrcard["resistances"]:
                if atkrtype == resistance["type"]:
                    dmg = dmg / 0.5
                    if debug_on:
                        log(f'[Pokemon][DEBUG] - {defrcard["name"]} is resistant against: {atkrtype}')
                    weak = False
                    resi = True
                    return int(dmg), weak, resi

        weak = False
        resi = False
        return dmg, weak, resi

    async def attack(self, atkr, defr):
        base_dmg = atkr["dmg"]  # base damage
        dmg = atkr["dmg"]
        attacker_type = atkr["card"]["types"][0]
        defender_type = defr["card"]["types"][0]

        # resistances and weakness check
        dmg, weak, resi, = await self.weak_n_res(attacker_type, defr["card"], dmg)

        # effectiveness calculations
        final_dmg, effect = await self.calculate_effectiveness(dmg, attacker_type, defender_type)
        if debug_on:
            log(f'[Pokemon][DEBUG] - {atkr["card"]["name"]}({atkr["hp"]}hp) uses {atkr["attack"]["name"]} -> {effect}{defr["card"]["name"]}({defr["hp"]}hp) takes {int(final_dmg)} damage (base {base_dmg})')
        if atkr["color"] == "green":
            await self.battlelogger(f'+ {atkr["card"]["name"]}({atkr["hp"]}hp) uses {atkr["attack"]["name"]} {"+" if weak else "-" if resi else ""}> {effect}{defr["card"]["name"]}({defr["hp"]}hp) takes {int(final_dmg)}({base_dmg}) dmg')
        else:
            await self.battlelogger(
                f'- {atkr["card"]["name"]}({atkr["hp"]}hp) uses {atkr["attack"]["name"]} {"+" if weak else "-" if resi else ""}> {effect}{defr["card"]["name"]}({defr["hp"]}hp) takes {int(final_dmg)}({base_dmg}) dmg')
        defr["hp"] -= int(final_dmg)

        # Check if the defender is dead
        if defr["hp"] <= 0:
            log(f'[Pokemon] - {defr["card"]["name"]} fainted!')
            if defr["color"] == "green":
                await self.battlelogger(f'+ {defr["card"]["name"]} fainted!')
            else:
                await self.battlelogger(f'- {defr["card"]["name"]} fainted!')
            return False  # If enemy is dead, return False
        return True  # If enemy is still alive, return True

    async def init_player_data(self, battlelist):
        # function gathers all relevant player data into the data dictionaries
        random_attack_names = ["Slap", "Punch", "Kick", "Fart", "Kiss"]
        default_attacks = [
            {'name': 'Slap', 'cost': ['Normal'], 'convertedEnergyCost': 1, 'damage': '10', 'text': ''},
            {'name': 'Punch', 'cost': ['Water', 'Colorless'], 'convertedEnergyCost': 2, 'damage': '10', 'text': ''},
            {'name': 'Kick', 'cost': ['Fighting'], 'convertedEnergyCost': 3, 'damage': '10', 'text': ''},
            {'name': 'Kiss', 'cost': ['Fairy'], 'convertedEnergyCost': 1, 'damage': '10', 'text': ''},
        ]
        # battlelist list with 2 lists one for each player
        # in each players list there is 2 elements the first one is the username(STR) the second is the card list
        # Select 3 cards for each player
        player1_cards = battlelist[0][1]
        player2_cards = battlelist[1][1]
        #player1_cards, player2_cards = self.pick_cards()

        # Printing out the details of the player's cards
        log("[Pokemon] - {}: {}".format(
            battlelist[0][0],  # Player 1's username
            ", ".join([f"{card['name']}({card['id']})" for card in player1_cards])
        ))

        log("[Pokemon] - {}: {}".format(
            battlelist[1][0],  # Player 2's username
            ", ".join([f"{card['name']}({card['id']})" for card in player2_cards])
        ))

        # Player 1 setup (handling each card separately)
        self.player1_data["player"] = battlelist[0][0]
        self.player1_data["cards"] = []
        self.player1_data["card_values"] = 0
        self.player1_data["color"] = "green"

        # Iterate through each of Player 1's cards
        for card in player1_cards:
            card_data = {"card": card, "hp": int(card["hp"]), "color": 'green'}

            # Find the best attack for the current card
            if card.get("attacks"):
                best_attack = max(
                    (attack for attack in card["attacks"]),
                    key=lambda attack: self.extract_damage_value(attack['damage'])
                )
            else:
                # if card dosent have an attack use a random generated one
                best_attack = random.choice(default_attacks)

            card_data["attack"] = best_attack
            card_data["dmg"] = self.extract_damage_value(best_attack["damage"])

            # reduced list changes to attacks
            if card_data["attack"]["name"] in halfed:
                card_data["dmg"] = int(card_data["dmg"] / 2)
                card_data["attack"]["name"] = card_data["attack"]["name"] + "(½)"
            if card_data["attack"]["name"] in threeforths:
                card_data["dmg"] = int(card_data["dmg"] * 3 / 4)
                card_data["attack"]["name"] = card_data["attack"]["name"] + "(¾)"

            self.player1_data["card_values"] = + int(card_data["dmg"])  # add up dmg to get hand value

            # add high damage attack to audit file if not in whitelist and not already handled
            if card_data["dmg"] > 125 and card_data["attack"]["name"] not in threeforths and card_data["attack"]["name"] not in halfed and card_data["attack"]["name"] not in whitelist:
                self.write_susattack(f'{card_data["attack"]["name"]} {card_data["dmg"]} dmg - {card["id"]}')

            # Append card data to the player's list of cards
            self.player1_data["cards"].append(card_data)

        # Player 2 setup (similar to Player 1)
        self.player2_data["player"] = battlelist[1][0]
        self.player2_data["cards"] = []
        self.player2_data["card_values"] = 0
        self.player2_data["color"] = "red"

        # Iterate through each of Player 2's cards
        for card in player2_cards:
            card_data = {"card": card, "hp": int(card["hp"]), "color": 'red'}

            # Find the best attack for the current card
            if card.get("attacks"):
                best_attack = max(
                    (attack for attack in card["attacks"]),
                    key=lambda attack: self.extract_damage_value(attack['damage'])
                )
            else:
                # if card dosent have an attack use a random generated one
                best_attack = random.choice(default_attacks)

            card_data["attack"] = best_attack
            card_data["dmg"] = self.extract_damage_value(best_attack["damage"])

            # reduced list changes to attacks
            if card_data["attack"]["name"] in halfed:
                card_data["dmg"] = int(card_data["dmg"] / 2)
                card_data["attack"]["name"] = card_data["attack"]["name"] + "(½)"
            if card_data["attack"]["name"] in threeforths:
                card_data["dmg"] = int(card_data["dmg"] * 3 / 4)
                card_data["attack"]["name"] = card_data["attack"]["name"] + "(¾)"

            self.player2_data["card_values"] = + int(card_data["dmg"])  # add up dmg to get hand value

            # add high damage attack to audit file if not in whitelist and not already handled
            if card_data["dmg"] > 125 and card_data["attack"]["name"] not in threeforths and card_data["attack"]["name"] not in halfed and card_data["attack"]["name"] not in whitelist:
                self.write_susattack(f'{card_data["attack"]["name"]} {card_data["dmg"]} dmg - {card["id"]}')

            # Append card data to the player's list of cards
            self.player2_data["cards"].append(card_data)

    async def combat_loop(self, battlelist):
        combat_on = False
        battle_loops = 0
        #self.battlelog = f'```diff'  # initialize/reset battlelog
        await self.init_player_data(battlelist)

        # combat loop
        combat_on = True
        turn_order = [self.player1_data, self.player2_data]
        random.shuffle(turn_order)
        log(f'[Pokemon] - {turn_order[0]["player"]} goes first!')
        if turn_order[0]["color"] == "green":
            await self.battlelogger(f'+ {turn_order[0]["player"]} goes first!', True, False)
        else:
            await self.battlelogger(f'- {turn_order[0]["player"]} goes first!', True, False)
        current_turn = 0

        # Initialize sent_out_cards dynamically based on player usernames
        sent_out_cards = {player_data["player"]: [] for player_data in turn_order}

        # Print the initial card announcement for both players
        for player_data in turn_order:
            active_card = player_data["cards"][0]  # Start with the first card for each player
            log(f'[Pokemon] - {player_data["player"]} sends out {active_card["card"]["name"]}!')
            if player_data["color"] == "green":
                await self.battlelogger(f'+ {player_data["player"]} sends out {active_card["card"]["name"]}!')
            else:
                await self.battlelogger(f'- {player_data["player"]} sends out {active_card["card"]["name"]}!')
            sent_out_cards[player_data["player"]].append(active_card["card"]["name"])

        while combat_on:
            # Get the current attacker and the next defender (circularly)
            attacker = turn_order[current_turn]
            defender = turn_order[(current_turn + 1) % len(turn_order)]  # Use modulo to rotate

            # Get the active card for both attacker and defender
            active_attacker_card = attacker["cards"][0]  # Start with the first card for each player
            active_defender_card = defender["cards"][0]

            # Print message if the card is being sent out for the first time
            if active_attacker_card["card"]["name"] not in sent_out_cards[attacker["player"]]:
                log(f'[Pokemon] - {attacker["player"]} sends out {active_attacker_card["card"]["name"]}!')
                if attacker["color"] == "green":
                    await self.battlelogger(f'+ {attacker["player"]} sends out {active_attacker_card["card"]["name"]}!')
                else:
                    await self.battlelogger(f'- {attacker["player"]} sends out {active_attacker_card["card"]["name"]}!')
                sent_out_cards[attacker["player"]].append(active_attacker_card["card"]["name"])

            # Perform the attack using the active attacker card and defender card
            result = await self.attack(active_attacker_card, active_defender_card)

            # Check if the defender's card is still alive (using the result of the attack)
            if not result:
                # If the defender's card is defeated, move on to the next card
                defender["cards"].pop(0)  # Remove the current card from the defender's list
                # send message to chat when a pokemon has fainted
                if len(defender["cards"]) == 0:
                    # If the defender has no cards left, the attacker wins
                    log(f'[Pokemon] - {attacker["player"]} wins!')
                    if attacker["color"] == "green":
                        await self.battlelogger(f'+ {attacker["player"]} wins!', False, True)
                    else:
                        await self.battlelogger(f'- {attacker["player"]} wins!', False, True)
                    combat_on = False
                    # send result end screen here
                    break

            # Switch turns by incrementing current_turn and using modulo to cycle through the players
            current_turn = (current_turn + 1) % len(turn_order)
            battle_loops += 1
            if battle_loops > 150:
                await self.battlelogger(f'ERROR, infinite loop detected', False, True)
                break

        stat_results = await self.handle_battle_outcome(attacker["player"], defender["player"], attacker["card_values"], defender["card_values"])
        return self.battlelog, stat_results, self.log_list

    async def battlelogger(self, log_input, start=False, end=False):
        if not start and not end:
            self.log_list.append(f'{log_input}\n')
        if start and not end:
            # first entry reset and add first input
            self.log_list = []
            self.log_list.append(f'{log_input}\n')
        if end and not start:
            # last entry
            self.log_list.append(f'{log_input}')
            total_characters = sum(len(string) for string in self.log_list)
            # disabled cause of rolling combat log
            #if total_characters > 1999:
            #    log(f'[Pokemon][DEBUG] - battle log exceeding 2000 characters, removing attack lines')
            #    self.log_list = [s for s in self.log_list if ">".lower() not in s.lower()]
            for entry in self.log_list:
                self.battlelog += entry

    def write_susattack(self, text):
        log(f'[Pokemon] - saving sus attack for later review -> susattacks.txt')
        with open(f'./local/pokemon/susttacks.txt', "a") as file:
            file.write(text + "\n")



