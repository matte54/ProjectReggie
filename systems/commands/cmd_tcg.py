import os
import json
import discord
import random
import time
import asyncio

from datetime import datetime, timedelta

from systems.logger import debug_on, log

from systems.varmanager import VarManager
from data.etc.admins import ADMINS

from systems.pokemon import pokemon
from systems.pokemon import pokehandler
from systems.pokemon import battle as bs
from systems.pokemon import channel_manager

from systems.pokemon.set_data import x as set_data
from systems.pokemon.rarity_data import x as rarity_data


class Tcg:
    picking_underway = False
    battle_underway = False
    battlelist = []
    battle_lock = asyncio.Lock()

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
        self.channelmanager = channel_manager.ChannelManager(self.client)
        self.bs = bs.Battle()
        self.varmanager = VarManager()
        self.admins = ADMINS

        self.set_id = None
        self.selected_cards = None
        self.userprofile_path = None
        self.pokemon_channels = []

        self.battletracker = {}
        self.battlelist = Tcg.battlelist

        self.subcommands = {
            "free": (self.free, False, False),
            "profile": (self.profile, False, False),
            "battle": (self.battle, False, False),
            "q": (self.query, True, False),
            "buy": (self.buy, True, False),
            "sell": (self.sell, True, False),
            "admin": (self.admin, True, True),
        }

    async def command(self, message):
        await self.collect_channel_ids()
        if message.channel.id not in self.pokemon_channels and message.author.id not in self.admins:
            # Channel does not allow Pokémon activity, return
            log(f'[Pokemon] - {message.channel.id} does not allow pokemon activity')
            return

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

        # Extract subcommand1, subcommand2, and subcommand3 (if present)
        subcommand1 = components[0]
        subcommand2 = components[1] if len(components) > 1 else None
        subcommand3 = components[2] if len(components) > 2 else None

        # Find the corresponding function for subcommand1
        handler_entry = self.subcommands.get(subcommand1)
        if handler_entry is None:
            await self.message.channel.send(f'```yaml\n\nSyntax error, unrecognized subcommand```')
            return

        handler, needs_subcommand2, has_optional_subcommand3 = handler_entry

        # Ensure subcommand2 is provided if required
        if needs_subcommand2 and subcommand2 is None:
            await self.message.channel.send(f'```yaml\n\nSyntax error, this subcommand needs an additional argument```')
            return

        # Call the handler with or without subcommands
        if has_optional_subcommand3:
            await handler(subcommand2, subcommand3)  # Pass `subcommand3` even if it is `None`
        elif needs_subcommand2:
            await handler(subcommand2)
        else:
            await handler()

    async def collect_channel_ids(self):
        if self.varmanager.read("pokemon_channels"):
            self.pokemon_channels = self.varmanager.read("pokemon_channels")

    async def send_to_all(self, msg):
        # send to this function to post to all pokemon channels
        for channel in self.pokemon_channels:
            ch = self.client.get_channel(channel)
            await ch.send(msg)

    def get_user_name(self, user_id):
        if os.path.exists(f'./data/etc/ids.json'):
            with open(f'./data/etc/ids.json', "r") as f:
                id_data = json.load(f)
            if str(user_id) in id_data:
                return id_data[str(user_id)]

    async def battle(self):
        log(f'[Pokemon][DEBUG] - Battle instance {id(self)} initiated by {self.username}')
        log(f'[Pokemon][DEBUG] - Battlelist has {len(Tcg.battlelist)} entries START OF SIGNUP')
        if Tcg.battle_underway:
            log(f"[Pokemon] - Battle already underway, ignoring request")
            return

        player_data = []

        if self.client.user.id == 327138137371574282:
            # check if user is allowed any more battles today
            if self.username in self.battletracker:
                if self.battletracker[self.username] >= 3:
                    await self.message.channel.send(
                        f'```yaml\n\nYou are not allowed any more battles today, come back tomorrow...```')
                    return

            # make sure user is not already signed up
            if Tcg.battlelist:
                if self.username in Tcg.battlelist[0]:
                    await self.message.channel.send(
                        f'```yaml\n\nYou are already signed up for battle```')
                    return
        else:
            log(f'[Pokemon] - client is {self.client.user.name} skipping signup rules')

        # check if user has cards to battle
        battlecards, found_cards, cardpaths = await self.check_card_avail()
        if not found_cards:
            await self.message.channel.send(
                f'```yaml\n\nYou dont own enough valid cards to battle```')
            return

        # create player data and append to the battlelist
        player_data.append(self.username)
        player_data.append(battlecards)
        Tcg.battlelist.append(player_data)
        log(f'[Pokemon][DEBUG] - Battlelist has {len(Tcg.battlelist)} entries')

        # add a daily entry to battles for the user
        self.battletracker[self.username] = self.battletracker.get(self.username, 0) + 1
        log(f'[Pokemon][DEBUG] - {self.battletracker}')

        signup_msg = f'```yaml\n\n{self.username} signed up for a Pokémon battle!\nBattle {self.battletracker[self.username]}/3 allowed for {self.username} today\n'
        if len(Tcg.battlelist) < 2:
            signup_msg += f'Use "$tcg battle" to challenge {self.username} to a pokémon battle!'
        signup_msg += f'```'
        await self.send_to_all(signup_msg)
        log(f'[Pokemon] - {self.username} signed up to battle {len(Tcg.battlelist)}/2 ready')

        # get card images and post to all pokechannels
        await self.get_battle_images(cardpaths)

        # if only one player is signed up stop here
        if len(Tcg.battlelist) < 2:
            return

        # attempt using async to have 1 battle and 1 battle only.. damn objects
        async with Tcg.battle_lock:
            # begin battle procedures
            Tcg.battle_underway = True

            await asyncio.sleep(10)
            await self.send_to_all(
                f'```yaml\n\nBattle starts in 10s - {Tcg.battlelist[0][0]} vs {Tcg.battlelist[1][0]}```')
            await asyncio.sleep(10)

            # try to block to catch battle exceptions for now
            try:
                fight, results, log_list = await self.bs.combat_loop(Tcg.battlelist)
                await self.rolling_combatlog(log_list)
            except Exception as e:
                log(f'[Pokemon] - an error has occurred: {e}')
                Tcg.battlelist = []  # clear the battle que
                Tcg.battle_underway = False
                await self.send_to_all(
                    f'```yaml\n\nsomething went wrong, someone call Matte 😭 (reseting battle '
                                                f'que)```')
                raise  # Re-raises the caught exception

            await self.send_to_all(results)
            Tcg.battlelist = []  # clear the battle que
            log(f'[Pokemon][DEBUG] - Battlelist has {len(Tcg.battlelist)} entries (AFTER CLEAR)')
            Tcg.battle_underway = False

    async def rolling_combatlog(self, loglist):
        max_lines = 10  # Maximum lines to display in the log
        time_between_lines = 3

        async def update_channel(channel_id):
            ch = self.client.get_channel(channel_id)
            rolling_log = []  # Each channel has its own rolling log

            # Send the initial message
            message = await ch.send(f'```diff\n\nBattle begins!```')

            try:
                for entry in loglist:
                    await asyncio.sleep(time_between_lines)  # Wait 5 seconds between updates

                    # Add the next line from the predefined log to the rolling log
                    rolling_log.append(entry)

                    # Trim the rolling log if it exceeds the maximum number of lines
                    if len(rolling_log) > max_lines:
                        rolling_log.pop(0)

                    # Update the message content
                    new_content = "```diff\n\n" + "".join(rolling_log) + '```'
                    await message.edit(content=new_content)

            except Exception as e:
                print(f"An error occurred in channel {channel_id}: {e}")

        # Run the update logic for each channel concurrently
        tasks = [update_channel(channel) for channel in self.pokemon_channels]
        await asyncio.gather(*tasks)

    async def check_card_avail(self):
        cardlist = []

        # Validate user profile and card count
        if not self.userprofile["profile"].get("last", ""):
            remaining = "NOW"
        if self.userprofile["profile"]["cards"] < 3:
            return cardlist, False

        # Filter sets with cards
        non_empty_bases = {base: values for base, values in self.userprofile["sets"].items() if values}
        if not non_empty_bases:
            return cardlist, False

        seen_cards = set()
        loopcounter = 0
        max_iterations = 50
        paths = []

        while len(cardlist) < 3 and loopcounter < max_iterations:
            loopcounter += 1

            # Select random base and card
            random_base = random.choice(list(non_empty_bases.keys()))
            base_dict = non_empty_bases[random_base]
            random_key = random.choice(list(base_dict.keys()))

            # Avoid duplicate selections
            if random_key in seen_cards:
                continue
            seen_cards.add(random_key)

            # Build file path and load card data
            setname = random_key.split('-')[0]
            filepath = os.path.join('./data/pokemon/sets', setname, f'{random_key}.json')

            try:
                with open(filepath, 'r', encoding='UTF-8') as json_file:
                    card_data = json.load(json_file)

                # Exclude "Trainer" cards
                if card_data["supertype"] == "Trainer":
                    continue

                # Append valid card to the list
                cardlist.append(card_data)
                paths.append(filepath.replace('sets', 'images').replace('.json', '.png'))

            except FileNotFoundError:
                continue  # Skip missing files

        return cardlist, len(cardlist) == 3, paths

    async def get_battle_images(self, imgpaths):
        pokecard_img_list = []
        for cardimage in imgpaths:
            normalized_path = os.path.normpath(cardimage)
            dir_path, filename = os.path.split(normalized_path)
            parent_dir = os.path.dirname(dir_path)
            new_dir_path = os.path.join(parent_dir, os.path.basename(dir_path), 'images')
            new_path = os.path.join(new_dir_path, filename)

            try:
                pokecard_img_list.append(new_path)
            except FileNotFoundError:
                # If the image is not found, use a default image
                log(f'[Pokemon] - Error, {new_path} not found!')
                pokecard_img_list.append(f'./data/pokemon/default_card.png')
        # send to all pokemon channels
        for channel in self.pokemon_channels:
            ch = self.client.get_channel(channel)
            files = [discord.File(file_path) for file_path in pokecard_img_list]
            await ch.send(files=files)

    async def free(self):
        if Tcg.picking_underway:
            log(f"[Pokemon] - Picking already underway, ignoring request")
            return
        # check time stamp
        if self.userprofile["profile"]["last"]:  # protection against a new profile without a time value
            time_since_last_pull = self.now - datetime.fromisoformat(self.userprofile["profile"]["last"])
            if not time_since_last_pull > timedelta(hours=24):
                remaining_time = timedelta(hours=24) - time_since_last_pull
                hours, remainder = divmod(remaining_time.total_seconds(), 3600)
                minutes = remainder // 60
                remaining = f"{int(hours)}h {int(minutes)}m"

                await self.message.channel.send(f'```yaml\n\nYou have {remaining} left until your daily free booster '
                                                f'pack...```')
                log(f'[Pokemon] - {self.username} has {remaining} remaining on freebie')
                return

        value = None
        self.set_id, rarityindex = await self.pokemon.pick_random_set()

        if os.path.exists(f'{self.setdata_path}{self.set_id}_setdata.json'):
            with open(f'{self.setdata_path}{self.set_id}_setdata.json', "r") as f:
                data = json.load(f)
        else:
            await self.message.channel.send(f'```yaml\n\nSet files not found (missing data)```')
            log(f'[Pokemon] - {self.setdata_path}{self.set_id}_setdata.json does not exist!')
            return

        Tcg.picking_underway = True  # set class var between objects

        # get the set value
        for item in self.setdatalist:
            if item[0] == self.set_id:
                value = item[2]

        log(f'[Pokemon] - {self.username} claims their daily free boosterpack')

        claimstring = f'```yaml\n\n{self.username} opens their daily FREE booster pack (10 cards) - ${value}\n{data["series"]} - {data["name"]}({self.set_id})\n'
        claimstring += f'Set contains {data["total"]} total cards, released {data["releaseDate"]}'
        if rarityindex < 0.4:
            claimstring += '\nThis set is a rare (more valueable) pull!'
        claimstring += '```'

        await self.message.channel.send(claimstring)
        try:
            self.selected_cards, card_img_list = await self.pokemon.process_input(self.set_id)
        except Exception as e:
            await self.send_to_all(
                f'```yaml\n\nsomething went wrong, someone call Matte 😭 (reseting)```')
            Tcg.picking_underway = False
            raise  # Re-raises the caught exception

        await self.message.channel.send(files=card_img_list)

        self.userprofile["profile"]["last"] = str(self.now.isoformat())
        summary_message = await self.handle_cards(0)

        await self.message.channel.send(summary_message)

        time.sleep(3)
        Tcg.picking_underway = False  # set class var between objects

    async def profile(self):
        log(f'[Pokemon] - {self.username} - requests their profile')
        # check when next free cast
        if not self.userprofile["profile"]["last"]:
            # this is here to protect against a blank string when the profile is new
            remaining = "NOW"
        else:
            time_since_last_pull = self.now - datetime.fromisoformat(self.userprofile["profile"]["last"])
            remaining_time = timedelta(hours=24) - time_since_last_pull

            if remaining_time.total_seconds() <= 0:
                remaining = "NOW"
            else:
                hours, remainder = divmod(remaining_time.total_seconds(), 3600)
                minutes = remainder // 60
                remaining = f"{int(hours)}h {int(minutes)}m"

        totalbattles = self.userprofile["profile"]["battles_won"] + self.userprofile["profile"]["battles_lost"]

        profilestring = f'```yaml\n\n'
        profilestring += f'***** {self.username.upper()}´S TCG PROFILE *****\n'
        profilestring += f'Money: ${self.userprofile["profile"]["money"]:.2f} Cards: {self.userprofile["profile"]["cards"]} Opened: {self.userprofile["profile"]["boosters_opened"]} Free: {remaining}\n'
        profilestring += f'Lvl: {self.userprofile["profile"]["level"]} Xp: {int(self.userprofile["profile"]["xp"])}/{int(self.userprofile["profile"]["xp_cap"])} Battles: {totalbattles} W:{self.userprofile["profile"]["battles_won"]} L:{self.userprofile["profile"]["battles_lost"]}\n'
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
            best_string += f'"{pokemon_name}" - ({cardid}) - ${value:.2f}\n'

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
                cards_owned, cards_total, id_list = await self.owned(subcommand2)
                print(id_list)
                with open(f'{self.setdata_path}{subcommand2}_setdata.json', "r") as f:
                    data = json.load(f)
                await self.message.channel.send(
                    f'```yaml\n\n{data["series"]} - {data["name"]}({subcommand2})\n'
                    f'Set contains {data["total"]} total cards, released {data["releaseDate"]}```')
                await self.message.author.send(f'```yaml\n\n*These are the cards you own in the {subcommand2} set*\n\n{id_list}```')
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
                try:
                    card_img = discord.File(card_img_path)
                except FileNotFoundError:
                    log(f'[Pokemon] - Error, {self.images_path}{set_id}/images/{set_id}-{card_id}.png not found!')
                    card_img = discord.File('./data/pokemon/default_card.png')

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
        if Tcg.picking_underway:
            log(f"[Pokemon] - Picking already underway, ignoring request")
            return

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

        try:
            self.selected_cards, card_img_list = await self.pokemon.process_input(subcommand2)
        except Exception as e:
            await self.send_to_all(
                f'```yaml\n\nsomething went wrong, someone call Matte 😭 (reseting)```')
            raise  # Re-raises the caught exception

        if not self.selected_cards:
            await self.message.channel.send(f'```yaml\n\nSet not found```')
            return
        self.set_id = subcommand2

        if os.path.exists(f'{self.setdata_path}{subcommand2}_setdata.json'):
            with open(f'{self.setdata_path}{subcommand2}_setdata.json', "r") as f:
                data = json.load(f)

        Tcg.picking_underway = True  # set class var between objects

        log(f'[Pokemon] - {self.username} buys the "{subcommand2}" boosterpack')
        await self.message.channel.send(
            f'```yaml\n\n{self.username} BUYS a booster pack (10 cards) - ${value}\n{data["series"]} - {data["name"]}({subcommand2})\n'
            f'Set contains {data["total"]} total cards, released {data["releaseDate"]}```')
        # post card images
        await self.message.channel.send(files=card_img_list)
        summary_message = await self.handle_cards(value)
        await self.setbroker()  # adjust set values
        await self.message.channel.send(summary_message)

        time.sleep(3)  # extra wait time for disk to spin up for getting images
        Tcg.picking_underway = False  # set class var between objects

    async def setbroker(self):
        # increasing prices of sets
        price_increase = random.uniform(1.2, 2.0)
        for i, item in enumerate(self.setdatalist):
            if item[0] == self.set_id:
                self.setdatalist[i] = (item[0], item[1], int(item[2] * price_increase))
                log(f'[Pokemon] - Increasing price of set {item[0]} from ${item[2]} to ${self.setdatalist[i][2]}')
                break

    async def handle_cards(self, set_cost):
        # define and zero catch info
        income = 0.0
        dupes = 0
        new = 0
        highv = []
        shighv = []
        uhighv = []

        # stamp profile stats
        self.userprofile["profile"]["boosters_opened"] += 1

        #subtract set cost if any
        if set_cost:
            #self.userprofile["profile"]["money"] -= round(set_cost, 2)
            await self.money_handler(-set_cost)
        # Extract relevant data
        trunc_list = [
            (card["id"], card["name"], card["rarity"], card["cardmarket"]["prices"]["averageSellPrice"])
            for card in self.selected_cards
        ]

        # Ensure the set structure exists
        self.userprofile.setdefault("sets", {}).setdefault(self.set_id, {})

        # Update user profile
        for card_id, name, rarity, sell_price in trunc_list:
            # some flare to the values of the cards
            if sell_price >= 30.0 and not sell_price > 99.0:
                log(f"[Pokemon] - {name}' ID {card_id} is a HIGH value card ({sell_price})")
                highv.append((card_id, name, sell_price))
            if sell_price >= 100.0 and not sell_price > 299.0:
                log(f"[Pokemon] - {name}' ID {card_id} is a SUPER HIGH value card ({sell_price})")
                shighv.append((card_id, name, sell_price))
            if sell_price >= 300.0:
                log(f"[Pokemon] - {name}' ID {card_id} is a ULTRA HIGH value card ({sell_price})")
                uhighv.append((card_id, name, sell_price))

            if card_id in self.userprofile["sets"][self.set_id]:
                # User already owns the card - sell or handle as needed
                # self.userprofile["profile"]["money"] += round(sell_price, 2)
                await self.money_handler(sell_price)
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
        #self.userprofile["profile"]["money"] = round(self.userprofile["profile"]["money"], 2)

        # Write updated profile to disk
        self.pokehandler.write_json(self.userprofile_path, self.userprofile)
        log(f"[Pokemon] - Updated profile written to {self.userprofile_path}!")
        if income > 0.0:
            log(f"[Pokemon] - {self.username} earned {round(income, 2)} from dupes")

        money_gained = round(income, 2)

        cards_owned, cards_total, id_list = await self.owned(self.set_id)

        # info about new cards or dupes and money gains here
        summary_message = f'||```yaml\n\n*** {self.username}s boosterpack summary ***\n'

        if highv:
            summary_message += f'{len(highv)} HIGH value card(s) pulled!\n'
            for card in highv:
                summary_message += f'{card[1]}({card[0]}) - ${card[2]}\n'
        if shighv:
            summary_message += f'{len(shighv)} SUPER HIGH value card(s) pulled!\n'
            for card in shighv:
                summary_message += f'{card[1]}({card[0]}) - ${card[2]}\n'
        if uhighv:
            summary_message += f'{len(uhighv)} ULTRA HIGH value card(s) pulled!\n'
            for card in uhighv:
                summary_message += f'{card[1]}({card[0]}) - ${card[2]}\n'

        if new:
            summary_message += f'{new} NEW cards '
        if dupes:
            summary_message += f'{dupes} dupes'
        if money_gained:
            summary_message += f'\n${money_gained} gained from selling dupes'
        summary_message += f'\nYou now own {cards_owned}/{cards_total} cards in this set'
        summary_message += f'```||'

        return summary_message

    async def owned(self, setid):
        # this function is flawed since i dont count trainers and energy THONK
        id_list = []
        cards_owned = len(self.userprofile["sets"][setid])
        with open(f'{self.setdata_path}/{setid}_setdata.json', "r") as f:
            data = json.load(f)
        cards_in_set = data["total"]
        id_list.extend(self.userprofile["sets"][setid].keys())
        id_list.sort()

        return cards_owned, cards_in_set, id_list

    async def money_handler(self, value):
        self.userprofile["profile"]["money"] += round(value, 2)

        self.pokehandler.write_json(self.userprofile_path, self.userprofile)
        log(f'[Pokemon] - {self.username} now has ${self.userprofile["profile"]["money"]} - Wrote {self.userprofile_path}!')

    async def find_json_files(self, directory):
        json_files = []
        for root, dirs, files in os.walk(directory):  # os.walk traverses directories recursively
            for file in files:
                if file.endswith('.json'):  # Check if the file has a .json extension
                    json_files.append(os.path.join(root, file))  # Get the full path
        return json_files

    async def sell(self, subcommand2):
        if "-" not in subcommand2:
            log(f'[Pokemon] - invalid card id')
            await self.message.channel.send(f'```yaml\n\nNot a valid CARD ID```')
            return
        set_match_found = False
        set_id, card_id = subcommand2.split("-")
        for t in self.setdatalist:
            if set_id == t[0]:
                set_match_found = True
                break

        if not set_match_found:
            log(f'[Pokemon] - set not found')
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
            pokemon_name = card_data["name"]
            try:
                check = self.userprofile['sets'][set_id][f'{set_id}-{card_id}']
                await self.message.channel.send(
                    f'```yaml\n\n{self.username} SOLD "{pokemon_name}" ({subcommand2}) card for ${card_value}```')
                del self.userprofile['sets'][set_id][f'{set_id}-{card_id}']
                await self.money_handler(card_value)
                log(f"[Pokemon] - {self.username} sold {pokemon_name}-{subcommand2} for {card_value}")
            except KeyError:
                log(f'[Pokemon] - {self.username} does not own this card')
                await self.message.channel.send(
                    f'```yaml\n\nYou do not own this card```')
        else:
            log(f'[Pokemon] - Card not found')
            await self.message.channel.send(
                f'```yaml\n\nCard not found```')

    async def admin(self, subcommand2, subcommand3=None):
        # reset the free timer
        if subcommand2 == "reset":
            # per command basis admin check
            if not self.message.author.id == self.admins[0]:
                log(f'[Pokemon] - {self.username} tried to get admin access and got denied')
                return

            user_profiles_list = await self.find_json_files('./local/pokemon/profiles/')
            for profile in user_profiles_list:
                with open(profile, "r") as f:
                    profile_data = json.load(f)
                profile_data["profile"]["last"] = ""
                self.pokehandler.write_json(profile, profile_data)
            log(f'[Pokemon][ADMIN] - {self.username} reset all free pulls')
            await self.send_to_all(f'```yaml\n\nADMIN {self.username} reset everyones free pack timer, pulls for all!```')
            return

        if subcommand2 == "test":
            # test section for debugging
            if not self.message.author.id == self.admins[0]:
                log(f'[Pokemon] - {self.username} tried to get admin access and got denied')
                return

            await self.owned("bw1")
            return

        if subcommand2 == "enable":
            if self.message.author.id not in self.admins:
                log(f'[Pokemon] - {self.username} tried to get admin access and got denied')
                return
            await self.channelmanager.enable(self.message)
            log(f'[Pokemon][ADMIN] - admin {self.username} ENABLED channel {self.message.channel.name}({self.message.channel.id}) for pokemon')
            return

        if subcommand2 == "disable":
            if self.message.author.id not in self.admins:
                log(f'[Pokemon] - {self.username} tried to get admin access and got denied')
                return
            await self.channelmanager.disable(self.message)
            log(f'[Pokemon][ADMIN] - admin {self.username} DISABLED channel {self.message.channel.name}({self.message.channel.id}) for pokemon')
            return

        if subcommand2 == "all":
            # give all active profiles "subcommand3" amount of money
            return

        await self.message.channel.send(
            f'```yaml\n\nAdmin command not recognized```')
