import os, json
import discord
from datetime import datetime, timedelta

from systems.logger import debug_on, log

from systems.varmanager import VarManager
from systems.pokemon import pokemon
from systems.pokemon import pokehandler

from systems.pokemon.set_data import x as set_data
from systems.pokemon.rarity_data import x as rarity_data


class Tcg:
    def __init__(self, client):
        # define paths
        self.setdata_path = "./data/pokemon/setdata/"
        self.sets_path = "./data/pokemon/sets/"
        self.images_path = "./data/pokemon/images/"
        self.profiles_path = "./local/pokemon/profiles/"

        self.setdatalist = set_data
        self.raritydatalist = rarity_data

        self.client = client
        self.message = None
        self.username = None
        self.userprofile = None
        self.now = None
        self.pokemon = pokemon.PokemonTCG(self.client)
        self.pokehandler = pokehandler.Pokehandler(self.client)
        self.varmanager = VarManager()

        self.set_id = None
        self.selected_cards = None
        self.userprofile_path = None

        self.subcommands = {
            "free": (self.free, False),
            "profile": (self.profile, False),
            "q": (self.query, True),
            "buy": (self.buy, True)
        }

    async def command(self, message):
        self.now = datetime.now()
        self.message = message
        self.username = self.get_user_name(message.author.id)
        log(f'[Pokemon] - USER: {self.username}')
        self.userprofile, self.userprofile_path = self.pokehandler.get_profile(message)
        content = message.content.lower()
        # Parse command
        components = content.lstrip("$tcg").split()
        if len(components) < 1:
            await self.message.channel.send(f'```yaml\n\nSyntax error, $tcg requires a subcommand```')
            return

        # Extract subcommand1 and subcommand2 (if present)
        subcommand1 = components[0]
        subcommand2 = components[1] if len(components) > 1 else None

        # Find the corresponding function for subcommand1
        handler_entry = self.subcommands.get(subcommand1)
        if handler_entry is None:
            await self.message.channel.send(f'```yaml\n\nSyntax error, unrecognized subcommand```')
            return

        handler, needs_subcommand2 = handler_entry

        # Ensure subcommand2 is provided if required
        if needs_subcommand2 and subcommand2 is None:
            await self.message.channel.send(f'```yaml\n\nSyntax error, this subcommand needs an additional argument```')
            return

        # Call the handler with or without subcommand2
        if needs_subcommand2:
            await handler(subcommand2)
        else:
            await handler()

    def get_user_name(self, user_id):
        if os.path.exists(f'./data/etc/ids.json'):
            with open(f'./data/etc/ids.json', "r") as f:
                id_data = json.load(f)
            if str(user_id) in id_data:
                return id_data[str(user_id)]

    async def free(self):
        # check time stamp
        if self.userprofile["profile"]["last"]:  # protection against a new profile without a time value
            time_since_last_pull = self.now - datetime.fromisoformat(self.userprofile["profile"]["last"])
            if not time_since_last_pull > timedelta(hours=24):
                remaining_time = timedelta(hours=24) - time_since_last_pull
                remaining_hours = remaining_time.total_seconds() / 3600

                await self.message.channel.send(f'```yaml\n\nYou have {remaining_hours:.2f} hours left until your daily free booster pack...```')
                log(f'[Pokemon] - {self.username} has {remaining_hours:.2f} hours remaining on freebie')
                return

        value = None
        self.set_id = await self.pokemon.pick_random_set()
        if os.path.exists(f'{self.setdata_path}{self.set_id}_setdata.json'):
            with open(f'{self.setdata_path}{self.set_id}_setdata.json', "r") as f:
                data = json.load(f)
        else:
            await self.message.channel.send(f'```yaml\n\nSet files not found (missing data)```')
            log(f'[Pokemon] - {self.setdata_path}{self.set_id}_setdata.json does not exist!')
            return

        # get the set value
        for item in self.setdatalist:
            if item[0] == self.set_id:
                value = item[2]

        log(f'[Pokemon] - {self.username} claims their daily free boosterpack')
        await self.message.channel.send(
            f'```yaml\n\n{self.username} opens their daily FREE booster pack (10 cards) - ${value}\n{data["series"]} - {data["name"]}({self.set_id})\n'
            f'Set contains {data["total"]} total cards, released {data["releaseDate"]}```')

        self.selected_cards, card_img_list = await self.pokemon.process_input(self.set_id)

        await self.message.channel.send(files=card_img_list)

        self.userprofile["profile"]["last"] = str(self.now.isoformat())
        summary_message = await self.handle_cards(0)

        await self.message.channel.send(summary_message)

    async def profile(self):
        log(f'[Pokemon] - {self.username} - requests their profile')
        # check when next free cast
        if not self.userprofile["profile"]["last"]:
            # this is here to protect against a blank string when the profile is new
            remaining = "NOW"
        else:
            time_since_last_pull = self.now - datetime.fromisoformat(self.userprofile["profile"]["last"])
            remaining_time = timedelta(hours=24) - time_since_last_pull
            remaining_hours = remaining_time.total_seconds() / 3600
            if remaining_hours < 0:
                remaining = "NOW"
            else:
                remaining = f'{remaining_hours:.2f}H'

        profilestring = f'```yaml\n\n'
        profilestring += f'***** {self.username.upper()}´S TCG PROFILE *****\n'
        profilestring += f'Money: ${self.userprofile["profile"]["money"]} Cards: {self.userprofile["profile"]["cards"]} Opened: {self.userprofile["profile"]["boosters_opened"]} Free: {remaining}\n'
        profilestring += f'***** TOP 10 MOST VALUEABLE CARDS OWNED *****\n'
        profilestring += await self.find_best()
        profilestring += f'```'
        await self.message.channel.send(profilestring)

    async def find_best(self):
        best_string = f''
        all_items = []
        for base_dict in self.userprofile["sets"].values():
            all_items.extend(base_dict.items())
        sorted_items = sorted(all_items, key=lambda item: item[1], reverse=True)[:10]

        # get names of all the cards
        for cardid, value in sorted_items:
            set_id, card_number = cardid.split("-")
            with open(f'{self.sets_path}{set_id}/{cardid}.json', "r") as f:
                card_data = json.load(f)
            pokemon_name = card_data["name"]
            best_string += f'"{pokemon_name}" - ({cardid}) - ${value}\n'

        return best_string

    async def query(self, subcommand2):
        log(f'[Pokemon] - {self.username} - sends QUERY: "{subcommand2}"')
        if subcommand2 == "sets":
            setstring = f'```yaml\n\n'
            # list of all sets and prices
            for x in self.setdatalist:
                setstring += f'{x[0]}(${x[2]})\n'
            setstring += f'```'
            # string is a mile long so send DM for now...
            await self.message.author.send(setstring)
            return

        if "-" not in subcommand2:
            # input must be a set query
            match_found = False
            for t in self.setdatalist:
                if subcommand2 == t[0]:
                    match_found = True
                    break
            if match_found:
                with open(f'{self.setdata_path}{subcommand2}_setdata.json', "r") as f:
                    data = json.load(f)
                await self.message.channel.send(
                    f'```yaml\n\n{data["series"]} - {data["name"]}({subcommand2})\n'
                    f'Set contains {data["total"]} total cards, released {data["releaseDate"]}```')
                return
            else:
                await self.message.channel.send(f'```yaml\n\nSet not found```')
                return

        if "-" in subcommand2:
            # input must be a card query
            set_match_found = False
            set_id, card_id = subcommand2.split("-")
            for t in self.setdatalist:
                if set_id == t[0]:
                    set_match_found = True
                    break

            if not set_match_found:
                await self.message.channel.send(f'```yaml\n\nSet not found```')
                return

            card_found = False
            for file in os.listdir(f'{self.sets_path}{set_id}'):
                if file.endswith(".json"):
                    if file == f'{set_id}-{card_id}.json':
                        card_found = True
                        break
            if card_found:
                card_path = f'{self.sets_path}{set_id}/{set_id}-{card_id}.json'
                with open(card_path, "r") as f:
                    card_data = json.load(f)
                card_value = card_data["cardmarket"]["prices"]["averageSellPrice"]
                card_img_path = f'{self.images_path}{set_id}/images/{set_id}-{card_id}.png'
                card_img = discord.File(card_img_path)

                await self.message.channel.send(file=card_img)

                try:
                    check = self.userprofile['sets'][set_id][f'{set_id}-{card_id}']
                    await self.message.channel.send(f'```yaml\n\nCard value: ${card_value} - {self.username} owns this card!```')
                except KeyError:
                    await self.message.channel.send(f'```yaml\n\nCard value: ${card_value} - {self.username} does not own this card.```')

            else:
                await self.message.channel.send(f'```yaml\n\ncard not found```')
                return

    async def buy(self, subcommand2):

        # get the set value
        for item in self.setdatalist:
            if item[0] == subcommand2:
                value = item[2]

        # get here if user can afford set
        if self.userprofile["profile"]["money"] < value:
            # user cant afford the set
            log(f"[Pokemon] - {self.username}s can not afford the set.")
            await self.message.channel.send(f'```yaml\n\nNot enough money, set cost is ${value} you only have ${self.userprofile["profile"]["money"]}```')
            return

        self.selected_cards, card_img_list = await self.pokemon.process_input(subcommand2)
        if not self.selected_cards:
            await self.message.channel.send(f'```yaml\n\nSet not found```')
            return
        self.set_id = subcommand2

        if os.path.exists(f'{self.setdata_path}{subcommand2}_setdata.json'):
            with open(f'{self.setdata_path}{subcommand2}_setdata.json', "r") as f:
                data = json.load(f)

        log(f'[Pokemon] - {self.username} buys the "{subcommand2}" boosterpack')
        await self.message.channel.send(
            f'```yaml\n\n{self.username} BUYS a booster pack (10 cards) - ${value}\n{data["series"]} - {data["name"]}({subcommand2})\n'
            f'Set contains {data["total"]} total cards, released {data["releaseDate"]}```')
        # post card images
        await self.message.channel.send(files=card_img_list)

        summary_message = await self.handle_cards(value)

        await self.message.channel.send(summary_message)

    async def handle_cards(self, set_cost):
        # define and zero catch info
        income = 0.0
        dupes = 0
        new = 0
        highv = []

        # stamp profile stats
        self.userprofile["profile"]["boosters_opened"] += 1

        #subtract set cost if any
        if set_cost:
            self.userprofile["profile"]["money"] -= round(set_cost, 2)

        # Extract relevant data
        trunc_list = [
            (card["id"], card["name"], card["rarity"], card["cardmarket"]["prices"]["averageSellPrice"])
            for card in self.selected_cards
        ]

        # Ensure the set structure exists
        self.userprofile.setdefault("sets", {}).setdefault(self.set_id, {})

        # Update user profile
        for card_id, name, rarity, sell_price in trunc_list:
            if sell_price > 30.0:
                log(f"[Pokemon] - {name}' ID {card_id} is a HIGH value card ({sell_price})")
                highv.append((card_id, name, sell_price))

            if card_id in self.userprofile["sets"][self.set_id]:
                # User already owns the card - sell or handle as needed
                self.userprofile["profile"]["money"] += round(sell_price, 2)
                income += round(sell_price, 2)
                dupes += 1
                log(f"[Pokemon] - {self.username}s already has '{name}({card_id})' selling.")
            else:
                # Add card to the user's profile
                new += 1
                self.userprofile["sets"][self.set_id][card_id] = sell_price
                self.userprofile["profile"]["cards"] += 1
                log(f"[Pokemon] - Added '{name}' ID {card_id} to {self.username}s profile.")

        # round off all money here before write
        self.userprofile["profile"]["money"] = round(self.userprofile["profile"]["money"], 2)

        # Write updated profile to disk
        self.pokehandler.write_json(self.userprofile_path, self.userprofile)
        log(f"[Pokemon] - Updated profile written to {self.userprofile_path}!")
        if income > 0.0:
            log(f"[Pokemon] - {self.username} earned {round(income, 2)} from dupes")

        money_gained = round(income, 2)

        # info about new cards or dupes and money gains here
        summary_message = f'||```yaml\n\n*** {self.username}s boosterpack summary ***\n'
        if highv:
            summary_message += f'{len(highv)} high value card(s) pulled!\n'
            for card in highv:
                summary_message += f'{card[1]}({card[0]}) - ${card[2]}\n'
        if new:
            summary_message += f'{new} NEW cards '
        if dupes:
            summary_message += f'{dupes} dupes'
        if money_gained:
            summary_message += f'\n${money_gained} gained from selling dupes'

        summary_message += f'```||'

        return summary_message

